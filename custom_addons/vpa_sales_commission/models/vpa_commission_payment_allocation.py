# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class VpaCommissionPaymentAllocation(models.Model):
    """Split of a payment on account across commission years.

    A payment made without a Commission Year link ("payment on account")
    can later be applied — fully or partially — to one or more commission
    years through these allocation lines. The unallocated remainder stays
    on account until it is applied.
    """
    _name = 'vpa.commission.payment.allocation'
    _description = 'Commission Payment Allocation'
    _order = 'payment_id desc, id'

    payment_id = fields.Many2one(
        'account.payment',
        string='Payment',
        required=True,
        ondelete='cascade',
        index=True,
        domain=[('payment_type', '=', 'outbound')],
    )
    scheme_year_id = fields.Many2one(
        'vpa.commission.scheme.year',
        string='Commission Year',
        required=True,
        ondelete='restrict',
        index=True,
    )
    amount = fields.Monetary(
        string='Allocated Amount',
        currency_field='currency_id',
        required=True,
        help='Portion of the payment (in the payment currency) applied to '
             'this commission year.',
    )
    currency_id = fields.Many2one(related='payment_id.currency_id')
    company_id = fields.Many2one(
        related='payment_id.company_id', store=True, index=True)
    employee_id = fields.Many2one(related='scheme_year_id.employee_id')
    payment_date = fields.Date(related='payment_id.date', string='Payment Date')
    payment_state = fields.Selection(related='payment_id.state', string='Payment Status')

    @api.constrains('amount', 'payment_id', 'scheme_year_id')
    def _check_allocation(self):
        for alloc in self:
            payment = alloc.payment_id
            currency = payment.currency_id
            if alloc.scheme_year_id.state == 'closed':
                # A closed year is reconciled: money landing in it afterwards
                # would silently move settled totals (same doctrine as the
                # closed-year guard on commission lines).
                raise ValidationError(_(
                    'Commission year %(year)s is closed. Reopen it before '
                    'applying payments to it.',
                    year=alloc.scheme_year_id.display_name,
                ))
            if currency.compare_amounts(alloc.amount, 0.0) <= 0:
                raise ValidationError(_(
                    'The allocated amount must be positive.'))
            if payment.payment_type != 'outbound':
                raise ValidationError(_(
                    'Only outbound (vendor) payments can be allocated to '
                    'commission years.'))
            if payment.commission_year_id:
                raise ValidationError(_(
                    'Payment %(payment)s is already fully linked to commission '
                    'year %(year)s. Remove the Commission Year link on the '
                    'payment before splitting it with allocations.',
                    payment=payment.display_name,
                    year=payment.commission_year_id.display_name,
                ))
            if (alloc.scheme_year_id.company_id and payment.company_id
                    and alloc.scheme_year_id.company_id != payment.company_id):
                raise ValidationError(_(
                    'The payment and the commission year belong to different '
                    'companies.'))
            total = sum(payment.commission_allocation_ids.mapped('amount'))
            if currency.compare_amounts(total, payment.amount) > 0:
                raise ValidationError(_(
                    'Total allocations (%(total)s) exceed the payment amount '
                    '(%(amount)s). Unallocated remainder cannot be negative.',
                    total=f'{total:,.2f} {currency.name}',
                    amount=f'{payment.amount:,.2f} {currency.name}',
                ))

    # ---- Chatter audit on the commission year ----
    @api.model_create_multi
    def create(self, vals_list):
        allocations = super().create(vals_list)
        for alloc in allocations:
            alloc.scheme_year_id.message_post(body=_(
                'Payment allocation added: %(amount)s from payment %(payment)s '
                '(unallocated remainder: %(rest)s).',
                amount=f'{alloc.amount:,.2f} {alloc.currency_id.name}',
                payment=alloc.payment_id.display_name,
                rest=f'{alloc.payment_id.commission_unallocated_amount:,.2f} '
                     f'{alloc.currency_id.name}',
            ))
        # Mirror the allocation into accounting: match the payment against the
        # year's posted bills, NEVER beyond the allocated amount. One sync per
        # unique (payment, year) pair — _applied_amount_pc reads ALL of the
        # payment's allocations, so duplicates in the batch add nothing.
        for payment, year in {(a.payment_id, a.scheme_year_id)
                              for a in allocations}:
            self._sync_payment_year_reconciliation(payment, year)
        return allocations

    def write(self, vals):
        """Editing an allocation (amount, year, payment) changes the sync
        inputs: guard closed years like create/unlink do, log the change,
        and resync every affected (payment, year) pair — before AND after
        values, so a retargeted allocation cleans up its old year."""
        touching = {'amount', 'scheme_year_id', 'payment_id'} & set(vals)
        pairs_before = set()
        if touching:
            for alloc in self:
                if alloc.scheme_year_id.state == 'closed':
                    raise ValidationError(_(
                        'Commission year %(year)s is closed. Reopen it before '
                        'changing payment allocations of it.',
                        year=alloc.scheme_year_id.display_name,
                    ))
                pairs_before.add((alloc.payment_id, alloc.scheme_year_id))
        res = super().write(vals)
        if touching:
            pairs_after = set()
            for alloc in self:
                if alloc.scheme_year_id.state == 'closed':
                    raise ValidationError(_(
                        'Commission year %(year)s is closed. Payments cannot '
                        'be allocated into it.',
                        year=alloc.scheme_year_id.display_name,
                    ))
                pairs_after.add((alloc.payment_id, alloc.scheme_year_id))
                alloc.scheme_year_id.message_post(body=_(
                    'Payment allocation updated: %(amount)s from payment '
                    '%(payment)s.',
                    amount=f'{alloc.amount:,.2f} {alloc.currency_id.name}',
                    payment=alloc.payment_id.display_name,
                ))
            for payment, year in pairs_before | pairs_after:
                self._sync_payment_year_reconciliation(payment, year)
        return res

    def unlink(self):
        resync = {(alloc.payment_id, alloc.scheme_year_id) for alloc in self}
        for alloc in self:
            if alloc.scheme_year_id.state == 'closed':
                raise ValidationError(_(
                    'Commission year %(year)s is closed. Reopen it before '
                    'removing payment allocations from it.',
                    year=alloc.scheme_year_id.display_name,
                ))
            alloc.scheme_year_id.message_post(body=_(
                'Payment allocation removed: %(amount)s from payment %(payment)s.',
                amount=f'{alloc.amount:,.2f} {alloc.currency_id.name}',
                payment=alloc.payment_id.display_name,
            ))
        res = super().unlink()
        # Re-sync accounting AFTER the allocation is gone: all matches between
        # the payment and that year's bills are rebuilt from the remaining
        # allocations (usually none -> fully unreconciled).
        for payment, year in resync:
            self._sync_payment_year_reconciliation(payment, year)
        return res

    # ------------------------------------------------------------------
    # Accounting mirror: payment <-> the year's posted commission bills
    # ------------------------------------------------------------------
    # Doctrine: the accounting match between a payment and a commission
    # year's bills must equal EXACTLY what the commission layer says is
    # applied to that year (allocations, or the full amount for a legacy
    # year-linked payment) — never more, never less (up to what the bills
    # can absorb). Everything here recomputes from scratch and is
    # idempotent: remove all matches for the (payment, year) pair, then
    # rebuild them capped at the applied amount.

    @api.model
    def _payment_payable_lines(self, payment):
        move = payment.move_id
        if not move or move.state != 'posted':
            return self.env['account.move.line'].sudo()
        return move.line_ids.filtered(
            lambda l: l.account_id.account_type == 'liability_payable')

    @api.model
    def _year_bill_payable_lines(self, year, posted_only=True):
        """The year's bill payable lines. posted_only=False widens the scope
        to draft/cancelled bills too — used by the CLEANUP step, so stale
        matches against a bill that was reset to draft are still found."""
        bills = year.bill_ids.filtered(
            lambda b: b.move_type == 'in_invoice'
            and (b.state == 'posted' or not posted_only))
        return bills.line_ids.filtered(
            lambda l: l.account_id.account_type == 'liability_payable'
        ).sorted(lambda l: (l.date, l.id))

    @api.model
    def _applied_amount_pc(self, payment, year):
        """What the commission layer applies from this payment to this year,
        in the payment currency. Deliberately NOT _payment_contribution:
        the sync must mirror explicit attachments only (year link or
        allocations), never legacy bill-matches — mirroring those would
        make the accounting justify itself."""
        if payment.commission_year_id == year:
            return payment.amount
        allocs = payment.commission_allocation_ids.filtered(
            lambda a: a.scheme_year_id == year)
        return sum(allocs.mapped('amount'))

    @api.model
    def _sync_payment_year_reconciliation(self, payment, year):
        """Rebuild the accounting matches between one payment and one year's
        posted bills so they equal the applied amount. Idempotent (wipe and
        rebuild for this pair only); no-ops for unposted payments.

        sudo throughout: this runs from triggers available to users without
        commission or full accounting rights (posting a bill, editing a
        payment); the scope is strictly the (payment, year) pair.
        """
        payment = payment.sudo()
        year = year.sudo()
        pay_lines = self._payment_payable_lines(payment)
        if not pay_lines:
            # Unposted payment: core already dropped any reconciliation when
            # the move left 'posted'; nothing to clean, nothing to build.
            return
        # 1. Drop every existing partial between this payment and ANY bill
        #    of the year — including draft ones (a posted bill can be reset
        #    to draft with its matches intact; scoping cleanup to posted
        #    bills would make those stale matches invisible forever).
        #    partial.unlink() is the widget's "unreconcile": it also removes
        #    full-reconciles and their exchange-difference entries.
        all_bill_moves = year.bill_ids
        partials = (pay_lines.matched_credit_ids | pay_lines.matched_debit_ids
                    ).filtered(
            lambda p: p.credit_move_id.move_id in all_bill_moves
            or p.debit_move_id.move_id in all_bill_moves)
        if partials:
            partials.sudo().unlink()
        # 2. Rebuild against POSTED bills, oldest first, capped at the
        #    applied amount.
        pc = payment.currency_id
        budget_pc = self._applied_amount_pc(payment, year)
        if pc.is_zero(budget_pc):
            return
        bill_lines = self._year_bill_payable_lines(year)
        company = payment.company_id or self.env.company
        cc = company.currency_id
        # Cash-basis companies: a hand-made partial would skip core's
        # cash-basis tax transfer. Commission bills carry no taxes today,
        # but stay conservative: only full (core) matches are made there.
        carve_allowed = not company.tax_exigibility
        self.env['account.move.line'].flush_model()

        def _residual_pc(line):
            return abs(line.amount_residual_currency) if line.currency_id \
                else abs(line.amount_residual)

        for pay_line in pay_lines:
            for bill_line in bill_lines:
                if pc.is_zero(budget_pc):
                    return
                pay_res_pc = _residual_pc(pay_line)
                pay_res_cc = abs(pay_line.amount_residual)
                bill_res_cc = abs(bill_line.amount_residual)
                if pc.is_zero(pay_res_pc) or cc.is_zero(bill_res_cc):
                    continue
                # RESIDUAL ratio, not booking ratio: prior partials at other
                # effective rates shift the line's remaining ratio, and the
                # cap must follow what reconciliation will actually consume.
                rate = (pay_res_cc / pay_res_pc) if pay_res_pc else 1.0
                budget_cc = cc.round(budget_pc * rate)
                natural_cc = min(cc.round(pay_res_pc * rate), bill_res_cc)
                if cc.compare_amounts(budget_cc, natural_cc) >= 0:
                    # Budget covers the whole natural match: STANDARD core
                    # reconcile (partials, full-reconciles, exchange diffs,
                    # cash basis — all core-handled). Decrement the budget by
                    # the MEASURED consumption, not a computed guess.
                    before_pc = _residual_pc(pay_line)
                    (pay_line | bill_line).sudo().reconcile()
                    self.env['account.move.line'].flush_model()
                    (pay_line | bill_line).invalidate_recordset(
                        ['amount_residual', 'amount_residual_currency',
                         'reconciled'])
                    consumed_pc = max(0.0, before_pc - _residual_pc(pay_line))
                    budget_pc = max(0.0, pc.round(budget_pc - consumed_pc))
                else:
                    # Budget is SMALLER than both open sides: carve an exact
                    # partial for just the budget. Amount fields follow
                    # core's contract: each *_amount_currency is expressed in
                    # ITS line's currency, derived from that line's own
                    # residual ratio. Neither line is exhausted (strict
                    # compare above), so no full-reconcile is due.
                    if not carve_allowed or cc.is_zero(budget_cc):
                        # Too small to represent, or cash-basis company:
                        # leave the remainder unmatched rather than risk an
                        # inconsistent partial.
                        return
                    debit_amount_currency = (
                        pc.round(budget_pc) if pay_line.currency_id
                        else budget_cc)
                    if bill_line.currency_id:
                        bill_res_bc = abs(bill_line.amount_residual_currency)
                        credit_amount_currency = bill_line.currency_id.round(
                            budget_cc * bill_res_bc / bill_res_cc)
                        if bill_line.currency_id.is_zero(credit_amount_currency):
                            return
                    else:
                        credit_amount_currency = budget_cc
                    if pay_line.currency_id and pc.is_zero(debit_amount_currency):
                        return
                    self.env['account.partial.reconcile'].sudo().create({
                        'debit_move_id': pay_line.id,
                        'credit_move_id': bill_line.id,
                        'amount': budget_cc,
                        'debit_amount_currency': debit_amount_currency,
                        'credit_amount_currency': credit_amount_currency,
                    })
                    self.env['account.move.line'].flush_model()
                    (pay_line | bill_line).invalidate_recordset(
                        ['amount_residual', 'amount_residual_currency',
                         'reconciled'])
                    return
