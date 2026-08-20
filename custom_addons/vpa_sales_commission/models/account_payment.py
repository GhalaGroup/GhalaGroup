# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    commission_year_id = fields.Many2one(
        'vpa.commission.scheme.year',
        string='Commission Year',
        index=True,
        copy=False,
        help='Links this FULL payment to an employee commission year. '
             'Set it when paying commission for a specific year, or leave empty '
             'for a payment on account. To apply only part of the payment (or '
             'split it across years), leave this empty and use Commission '
             'Allocations instead.',
    )
    commission_allocation_ids = fields.One2many(
        'vpa.commission.payment.allocation',
        'payment_id',
        string='Commission Allocations',
        copy=False,
    )
    commission_allocated_amount = fields.Monetary(
        string='Allocated to Commission',
        currency_field='currency_id',
        compute='_compute_commission_allocation',
        store=True,
    )
    commission_unallocated_amount = fields.Monetary(
        string='Unallocated (On Account)',
        currency_field='currency_id',
        compute='_compute_commission_allocation',
        store=True,
        help='Part of this payment not yet applied to any commission year.',
    )
    commission_has_allocations = fields.Boolean(
        string='Has Commission Allocations',
        compute='_compute_commission_has_allocations',
        help='Whether this payment is split across commission years. Exists so '
             'the payment form can test this WITHOUT naming '
             'commission_allocation_ids in a view expression: the standard form '
             'is seen by every user, and the web client fetches whatever a '
             'modifier references, which raises AccessError for anyone without '
             'commission access. Computed with sudo, so it is safe to read.',
    )
    commission_allocated_years = fields.Char(
        string='Allocated To',
        compute='_compute_commission_allocated_years',
        help='Commission years this payment is applied to through allocations, '
             'with the amount applied to each. Empty for payments linked to a '
             'single year via Commission Year, and for unallocated payments.',
    )
    commission_employee_partner_ids = fields.Many2many(
        'res.partner',
        string='Commission Employees',
        compute='_compute_commission_employee_partners',
        help='Work-contact partners of employees who have a commission scheme. '
             'Used to restrict the Vendor field to commission employees on the '
             'commission payment form.',
    )

    @api.depends('commission_allocation_ids')
    def _compute_commission_has_allocations(self):
        for pay in self:
            pay.commission_has_allocations = bool(pay.sudo().commission_allocation_ids)

    @api.depends('commission_allocation_ids.scheme_year_id',
                 'commission_allocation_ids.amount')
    def _compute_commission_allocated_years(self):
        for pay in self:
            # sudo: same standard-form exposure as the other commission computes.
            # formatLang: locale digits + currency symbol + correct decimal
            # places — a hardcoded ',.2f' hid the currency entirely in the
            # multi-currency payment list this column exists to clarify.
            allocs = pay.sudo().commission_allocation_ids
            pay.commission_allocated_years = ', '.join(
                f"{a.scheme_year_id.year}: "
                f"{formatLang(self.env, a.amount, currency_obj=a.currency_id)}"
                for a in allocs
            ) or False

    @api.depends_context('company')
    def _compute_commission_employee_partners(self):
        # Employees that have a commission scheme (any year) in the allowed
        # companies, resolved to their work-contact partner.
        # sudo: this field is injected (invisible) into the STANDARD payment
        # form, so it computes for every user who opens any payment. Only
        # commission managers may read vpa.commission.scheme, so an unprivileged
        # read raises AccessError and blocks the payment form entirely. Reading
        # with sudo exposes nothing but which partners are commission employees,
        # and only to build the vendor domain on the commission payment form.
        schemes = self.env['vpa.commission.scheme'].sudo().search([])
        partners = schemes.employee_id.work_contact_id
        for pay in self:
            pay.commission_employee_partner_ids = partners

    @api.depends('amount', 'commission_allocation_ids.amount', 'commission_year_id')
    def _compute_commission_allocation(self):
        for pay in self:
            # sudo: computed on every payment form load, including for users
            # with no commission access (see _compute_commission_employee_partners).
            allocated = sum(pay.sudo().commission_allocation_ids.mapped('amount'))
            pay.commission_allocated_amount = allocated
            # A full-year link consumes the whole payment.
            if pay.commission_year_id:
                pay.commission_unallocated_amount = 0.0
            else:
                pay.commission_unallocated_amount = pay.amount - allocated

    @api.constrains('commission_year_id')
    def _check_commission_year_vs_allocations(self):
        for pay in self:
            # sudo: constraints fire on every create/write of a payment,
            # including by users with no commission access.
            if pay.commission_year_id and pay.sudo().commission_allocation_ids:
                raise ValidationError(_(
                    'Payment %(payment)s has commission allocations. A payment '
                    'is either fully linked to one year (Commission Year) or '
                    'split via allocations — not both.',
                    payment=pay.display_name,
                ))
            if pay.commission_year_id and pay.sudo().commission_year_id.state == 'closed':
                raise ValidationError(_(
                    'Commission year %(year)s is closed. Reopen it before '
                    'assigning payments to it.',
                    year=pay.commission_year_id.display_name,
                ))

    def write(self, vals):
        # Assigning/unassigning a payment to a commission year is a money
        # movement between year cards: log it on the year(s), refuse to
        # quietly pull cash out of a CLOSED (reconciled) year, and keep the
        # accounting matches against the year's bills in sync (built on
        # assign, removed on unassign).
        year_moves = []
        if 'commission_year_id' in vals:
            Year = self.env['vpa.commission.scheme.year'].sudo()
            new_year = Year.browse(vals['commission_year_id']) if vals.get('commission_year_id') else Year
            sudo_self = self.sudo()
            for pay, sudo_pay in zip(self, sudo_self):
                old_year = sudo_pay.commission_year_id
                year_moves.append((pay, old_year))
                if old_year and old_year != new_year:
                    if old_year.state == 'closed':
                        raise ValidationError(_(
                            'Payment %(payment)s is linked to the closed '
                            'commission year %(year)s. Reopen the year before '
                            'unassigning the payment.',
                            payment=pay.display_name,
                            year=old_year.display_name,
                        ))
                    old_year.message_post(body=_(
                        'Payment %(payment)s (%(amount)s) unassigned from this year.',
                        payment=pay.display_name,
                        amount=formatLang(self.env, pay.amount, currency_obj=pay.currency_id),
                    ))
                if new_year and old_year != new_year:
                    new_year.message_post(body=_(
                        'Payment %(payment)s (%(amount)s) assigned to this year.',
                        payment=pay.display_name,
                        amount=formatLang(self.env, pay.amount, currency_obj=pay.currency_id),
                    ))
        res = super().write(vals)
        if year_moves:
            Allocation = self.env['vpa.commission.payment.allocation'].sudo()
            for pay, old_year in year_moves:
                new_year = pay.sudo().commission_year_id
                if old_year == new_year:
                    continue
                if old_year:
                    Allocation._sync_payment_year_reconciliation(pay, old_year)
                if new_year:
                    Allocation._sync_payment_year_reconciliation(pay, new_year)
        return res

    def _commission_revert_from_year(self, year):
        """THE revert rule, in one place (used by the list button and the
        year dialog): detach this payment from ``year`` whichever way it is
        attached. Chatter, closed-year guards and the accounting un-match run
        through the normal write/unlink paths. Returns True if anything was
        detached. Reminds about write-offs, which are NOT auto-unwound."""
        self.ensure_one()
        touched = False
        if self.commission_year_id == year:
            self.commission_year_id = False
            touched = True
        allocs = self.sudo().commission_allocation_ids.filtered(
            lambda a: a.scheme_year_id == year)
        if allocs:
            allocs.unlink()
            touched = True
        if touched:
            writeoffs = self.env['account.move'].sudo().search_count([
                ('commission_year_id', '=', year.id),
                ('commission_writeoff', '=', True),
                ('state', '=', 'posted'),
            ])
            if writeoffs:
                year.sudo().message_post(body=_(
                    'Note: %(count)d posted rounding write-off entr(y/ies) '
                    'exist for this year and were NOT reverted with payment '
                    '%(payment)s — review them if this settlement is undone.',
                    count=writeoffs, payment=self.display_name))
        return touched

    def action_commission_revert_from_year(self):
        """One-click revert from the year's payments list: pull this payment
        back OUT of the year it was opened from (context carries the year).

        Handles both attachment kinds: clears a full-year link, deletes the
        allocation(s) to that year. Chatter logging and the closed-year guard
        apply through the normal write/unlink paths. Manager-only (button
        group), and the money returns on account for re-allocation."""
        year_id = self.env.context.get('commission_revert_year_id')
        if not year_id:
            raise ValidationError(_(
                'Open the payments from a commission year to revert from it.'))
        year = self.env['vpa.commission.scheme.year'].browse(year_id)
        reverted = self.env['account.payment']
        for pay in self:
            if pay._commission_revert_from_year(year):
                reverted |= pay
        if not reverted:
            raise ValidationError(_(
                'This payment is not assigned to %(year)s — nothing to revert.',
                year=year.display_name))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': _('Payment Reverted'),
                'message': _(
                    '%(count)d payment(s) removed from %(year)s — the money '
                    'is back on account and can be allocated again.',
                    count=len(reverted), year=year.display_name),
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
            },
        }

    # ---- Journal transaction (bank statement line) for easy reconciliation ----
    commission_has_journal_transaction = fields.Boolean(
        string='Journal Transaction Created',
        compute='_compute_commission_has_journal_transaction',
        help='Whether a matching journal transaction (statement line) already '
             'exists for this commission payment.',
    )
    commission_show_add_transaction = fields.Boolean(
        compute='_compute_commission_has_journal_transaction',
        help='Show the "Add to Journal Transactions" button: a cash-journal '
             'commission payment that has no statement line yet.',
    )
    commission_is_payment = fields.Boolean(
        string='Is Commission Payment',
        compute='_compute_commission_is_payment',
        help='Whether this is a commission payment (year-linked, allocated, or '
             'an on-account payment to a commission employee). Drives the '
             'Print Voucher button.',
    )

    @api.depends('commission_year_id', 'commission_allocation_ids',
                 'partner_id', 'payment_type', 'commission_employee_partner_ids')
    def _compute_commission_is_payment(self):
        for pay in self:
            pay.commission_is_payment = pay._is_commission_payment()

    def _is_commission_payment(self):
        """A payment counts as a commission payment if it is linked/allocated to
        a commission year, OR it is an outbound payment to a commission
        employee's work-contact (covers on-account payments awaiting
        allocation)."""
        self.ensure_one()
        # sudo on the allocations: this runs for every user opening a payment
        if self.commission_year_id or self.sudo().commission_allocation_ids:
            return True
        return bool(
            self.payment_type == 'outbound'
            and self.partner_id
            and self.partner_id in self.commission_employee_partner_ids
        )

    @api.depends('journal_id', 'state', 'commission_year_id',
                 'commission_allocation_ids', 'name', 'partner_id',
                 'commission_employee_partner_ids')
    def _compute_commission_has_journal_transaction(self):
        StmtLine = self.env['account.bank.statement.line']
        for pay in self:
            has_txn = False
            if pay.name and pay.name != '/':
                has_txn = bool(StmtLine.sudo().search_count([
                    ('journal_id', '=', pay.journal_id.id),
                    ('payment_ref', '=', pay.memo or pay.name),
                ]))
            pay.commission_has_journal_transaction = has_txn
            pay.commission_show_add_transaction = (
                pay._is_commission_payment()
                and pay.journal_id.type == 'cash'
                and pay.state in ('in_process', 'paid')
                and not has_txn
            )

    def action_add_journal_transaction(self):
        """Create the (unreconciled) statement line mirroring this commission
        payment, so it appears in the journal's transaction list ready to
        reconcile — the same helper the Pay-Year wizard uses."""
        self.ensure_one()
        if self.commission_has_journal_transaction:
            raise ValidationError(_(
                'A journal transaction already exists for %(payment)s.',
                payment=self.display_name,
            ))
        journal = self.journal_id
        vals = {
            'journal_id': journal.id,
            'date': self.date,
            'payment_ref': self.memo or self.name,
            'partner_id': self.partner_id.id,
        }
        if not journal.currency_id or journal.currency_id == self.currency_id:
            # Journal in the payment currency (or company-currency journal paid
            # in company currency): statement amount is the payment amount.
            vals['amount'] = -self.amount
        else:
            # Currency-less journal paid in a foreign currency: statement amount
            # is in company currency, foreign amount carried alongside.
            company = self.company_id or self.env.company
            vals['amount'] = -self.currency_id._convert(
                self.amount, company.currency_id, company, self.date,
            )
            vals['foreign_currency_id'] = self.currency_id.id
            vals['amount_currency'] = -self.amount
        # sudo: statement-line creation needs full accounting rights that a
        # commission manager doesn't have. Safe: manager-only button, journal
        # is the payment's own journal.
        self.env['account.bank.statement.line'].sudo().create(vals)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': _('Journal Transaction Added'),
                'message': _('A transaction for %(payment)s was added to the '
                             '%(journal)s transaction list.',
                             payment=self.name, journal=self.journal_id.name),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

