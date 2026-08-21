# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class VpaCommissionApplyPaymentWizard(models.TransientModel):
    """Apply on-account payments (fully or partially) to a commission year.

    Reconciliation-style: every eligible on-account payment is listed as a
    row; the user ticks the ones to apply and can adjust the amount per row.
    One allocation is created per ticked row.
    """
    _name = 'vpa.commission.apply.payment.wizard'
    _description = 'Apply On-Account Payment to Commission Year'

    scheme_year_id = fields.Many2one(
        'vpa.commission.scheme.year',
        string='Commission Year',
        required=True,
        readonly=True,
    )
    employee_id = fields.Many2one(related='scheme_year_id.employee_id')
    company_id = fields.Many2one(related='scheme_year_id.company_id')
    currency_id = fields.Many2one(related='scheme_year_id.currency_id')
    # Uses the same figure as the Commission Centre card ("Still to pay" =
    # Total to Pay − paid), NOT the approved-only outstanding — showing a
    # different "outstanding" here than on the card the user just came from
    # made correct numbers look wrong.
    outstanding_cash = fields.Monetary(
        related='scheme_year_id.still_to_pay_total',
        string='Still to Pay (Year)',
        currency_field='currency_id',
    )

    line_ids = fields.One2many(
        'vpa.commission.apply.payment.wizard.line',
        'wizard_id',
        string='On-Account Payments',
    )
    applied_line_ids = fields.One2many(
        'vpa.commission.apply.payment.wizard.applied',
        'wizard_id',
        string='Applied Payments',
    )
    total_to_apply = fields.Monetary(
        string='Total to Apply',
        currency_field='currency_id',
        compute='_compute_totals',
        help='Sum of the ticked rows, converted to the commission currency '
             'at each payment\'s date.',
    )
    outstanding_after = fields.Monetary(
        string='Outstanding After',
        currency_field='currency_id',
        compute='_compute_totals',
        help='The year\'s outstanding once the ticked amounts are applied. '
             'Negative means overpaid (advance).',
    )

    @api.model
    def _get_eligible_payments(self, scheme_year):
        """On-account payments that can be applied to this year — the same
        definition the year card's "Not allocated" badge uses (shared domain
        helper on the scheme year), so card and wizard never disagree."""
        Payment = self.env['account.payment']
        company_ids = [scheme_year.company_id.id]
        # Prefer payments made to the employee; fall back to all on-account
        # payments if none match (e.g. paid to another party).
        partner = scheme_year.employee_id.work_contact_id
        payments = Payment
        if partner:
            payments = Payment.search(
                scheme_year._onaccount_payment_domain(company_ids, [partner.id]),
                order='date, id')
        if not payments:
            payments = Payment.search(
                scheme_year._onaccount_payment_domain(company_ids),
                order='date, id')
        return payments

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # Guard on active_model: active_ids may belong to another model
        # (the client injects them from whatever view launched the action).
        if (not res.get('scheme_year_id')
                and self.env.context.get('active_model') == 'vpa.commission.scheme.year'
                and self.env.context.get('active_id')):
            res['scheme_year_id'] = self.env.context['active_id']
        year_id = res.get('scheme_year_id')
        if year_id and 'line_ids' not in res:
            scheme_year = self.env['vpa.commission.scheme.year'].browse(year_id)
            res['line_ids'] = [(0, 0, {'payment_id': p.id})
                               for p in self._get_eligible_payments(scheme_year)]
            # Payments already applied to this year, both attachment kinds —
            # each can be ticked for a one-click revert in the same dialog.
            applied = [(0, 0, {
                'payment_id': p.id,
                'kind': 'year',
                'amount_applied': p.amount,
            }) for p in scheme_year.payment_ids]
            applied += [(0, 0, {
                'payment_id': a.payment_id.id,
                'kind': 'alloc',
                'allocation_id': a.id,
                'amount_applied': a.amount,
            }) for a in scheme_year.allocation_ids]
            res['applied_line_ids'] = applied
        return res

    def _to_scheme_currency(self, amount, payment):
        """Convert a payment-currency amount to the scheme currency at the
        payment's own date — the doctrine used everywhere in this module."""
        self.ensure_one()
        if (payment.currency_id and self.currency_id
                and payment.currency_id != self.currency_id):
            return payment.currency_id._convert(
                amount, self.currency_id,
                self.company_id or self.env.company,
                payment.date or fields.Date.today(),
            )
        return amount

    @api.depends('line_ids.select', 'line_ids.amount_to_apply',
                 'line_ids.payment_id', 'scheme_year_id')
    def _compute_totals(self):
        for wiz in self:
            total = sum(
                wiz._to_scheme_currency(l.amount_to_apply, l.payment_id)
                for l in wiz.line_ids.filtered('select'))
            wiz.total_to_apply = total
            wiz.outstanding_after = (
                (wiz.scheme_year_id.still_to_pay_total or 0.0) - total)

    def action_apply(self):
        self.ensure_one()
        lines = self.line_ids.filtered('select')
        if not lines:
            raise UserError(_(
                'Tick at least one on-account payment to apply. (Reverting an '
                'applied payment happens instantly with its Revert button.)'))
        # Validate and create in ONE pass over exactly the ticked rows — a
        # ticked row with a zero/negative amount must raise, never be silently
        # skipped, or the preview totals and the created allocations disagree.
        Allocation = self.env['vpa.commission.payment.allocation']
        for line in lines:
            currency = line.payment_currency_id
            if currency.compare_amounts(line.amount_to_apply, 0.0) <= 0:
                raise UserError(_(
                    '%(payment)s is ticked with no amount to apply. Set a '
                    'positive amount, or untick the row.',
                    payment=line.payment_id.display_name,
                ))
            if currency.compare_amounts(
                    line.amount_to_apply,
                    line.payment_id.commission_unallocated_amount) > 0:
                raise UserError(_(
                    '%(payment)s: you cannot apply %(amount)s — only %(rest)s '
                    'of this payment is still unallocated.',
                    payment=line.payment_id.display_name,
                    amount=f'{line.amount_to_apply:,.2f} {currency.name}',
                    rest=f'{line.payment_id.commission_unallocated_amount:,.2f} '
                         f'{currency.name}',
                ))
            Allocation.create({
                'payment_id': line.payment_id.id,
                'scheme_year_id': self.scheme_year_id.id,
                'amount': line.amount_to_apply,
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': _('Payments Applied'),
                'message': _(
                    '%(count)d payment(s) applied to %(year)s.',
                    count=len(lines),
                    year=self.scheme_year_id.display_name,
                ),
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
            },
        }


class VpaCommissionApplyPaymentWizardLine(models.TransientModel):
    _name = 'vpa.commission.apply.payment.wizard.line'
    _description = 'Apply On-Account Payment Wizard Line'
    _order = 'id'

    wizard_id = fields.Many2one(
        'vpa.commission.apply.payment.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    select = fields.Boolean(string='Apply')
    payment_id = fields.Many2one(
        'account.payment',
        string='Payment',
        required=True,
        readonly=True,
    )
    date = fields.Date(related='payment_id.date', string='Date')
    memo = fields.Char(related='payment_id.memo', string='Memo')
    journal_id = fields.Many2one(related='payment_id.journal_id', string='Journal')
    partner_id = fields.Many2one(related='payment_id.partner_id', string='Paid To')
    payment_currency_id = fields.Many2one(
        related='payment_id.currency_id', string='Payment Currency')
    payment_amount = fields.Monetary(
        related='payment_id.amount',
        string='Payment Total',
        currency_field='payment_currency_id',
    )
    unallocated_amount = fields.Monetary(
        related='payment_id.commission_unallocated_amount',
        string='Still Unallocated',
        currency_field='payment_currency_id',
    )
    amount_to_apply = fields.Monetary(
        string='Amount to Apply',
        currency_field='payment_currency_id',
        help='Portion of this payment (in the payment currency) to apply to '
             'the commission year. Defaults to the full unallocated remainder '
             'when the row is ticked.',
    )

    @api.onchange('select')
    def _onchange_select(self):
        """Ticking a row prefills what the YEAR still needs, capped at the
        payment's unallocated remainder — never more. Applying beyond the
        year's outstanding must be a deliberate act (type the amount by
        hand), not the default: the prefill used to offer the full payment
        and one click overpaid the year. Unticking clears the amount so the
        totals always reflect the ticked rows."""
        # No early return inside the loop: every line in self must be
        # processed (a skipped untick would keep a stale amount); the first
        # warning is collected and returned at the end.
        warning = None
        for line in self:
            if line.select and not line.amount_to_apply:
                wiz = line.wizard_id
                # Remaining need in the scheme currency: the year's still-to-
                # pay minus what the OTHER ticked rows already cover
                # (outstanding_after excludes this line while its amount is 0).
                remaining = max(0.0, wiz.outstanding_after)
                if (line.payment_currency_id and wiz.currency_id
                        and line.payment_currency_id != wiz.currency_id):
                    remaining = wiz.currency_id._convert(
                        remaining, line.payment_currency_id,
                        wiz.company_id or self.env.company,
                        line.payment_id.date or fields.Date.today(),
                    )
                line.amount_to_apply = min(line.unallocated_amount, remaining)
                if line.payment_currency_id.is_zero(line.amount_to_apply):
                    # Say it NOW, not as a cryptic error on Apply: the year
                    # needs nothing, so the capped prefill is zero.
                    line.select = False
                    warning = warning or {
                        'title': _('Nothing left to pay for this year'),
                        'message': _(
                            '%(year)s is fully covered — applying %(payment)s '
                            'would overpay it, so the row was unticked. To pay '
                            'a deliberate advance into this year, type the '
                            'amount yourself in "Amount to Apply".',
                            year=wiz.scheme_year_id.display_name,
                            payment=line.payment_id.display_name,
                        ),
                    }
            elif not line.select:
                line.amount_to_apply = 0.0
        if warning:
            return {'warning': warning}

    @api.onchange('amount_to_apply')
    def _onchange_amount_to_apply(self):
        """Typing an amount counts as selecting the row."""
        for line in self:
            if line.amount_to_apply and not line.select:
                line.select = True


class VpaCommissionApplyPaymentWizardApplied(models.TransientModel):
    """A payment already applied to the year — tickable for one-click revert."""
    _name = 'vpa.commission.apply.payment.wizard.applied'
    _description = 'Applied Payment (Revert Candidate)'
    _order = 'id'

    wizard_id = fields.Many2one(
        'vpa.commission.apply.payment.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    payment_id = fields.Many2one(
        'account.payment',
        string='Payment',
        required=True,
        readonly=True,
    )
    date = fields.Date(related='payment_id.date', string='Date')
    memo = fields.Char(related='payment_id.memo', string='Memo')
    journal_id = fields.Many2one(related='payment_id.journal_id', string='Journal')
    payment_currency_id = fields.Many2one(
        related='payment_id.currency_id', string='Payment Currency')
    kind = fields.Selection([
        ('year', 'Whole payment'),
        ('alloc', 'Allocation'),
    ], string='Applied As', readonly=True)
    allocation_id = fields.Many2one(
        'vpa.commission.payment.allocation',
        string='Allocation',
        readonly=True,
    )
    amount_applied = fields.Monetary(
        string='Applied Amount',
        currency_field='payment_currency_id',
        readonly=True,
    )

    def action_revert_now(self):
        """Instant one-click revert of this applied payment — no tick, no
        Apply button. Delegates to THE revert rule on account.payment
        (chatter, closed-year guards and the accounting un-match run through
        the normal paths) and reopens the dialog fresh, so the payment
        reappears in the on-account table with the totals updated."""
        self.ensure_one()
        wiz = self.wizard_id
        self.payment_id._commission_revert_from_year(wiz.scheme_year_id)
        return wiz.scheme_year_id.action_apply_payment()
