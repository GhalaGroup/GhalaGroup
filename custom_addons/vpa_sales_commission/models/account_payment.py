# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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
    commission_employee_partner_ids = fields.Many2many(
        'res.partner',
        string='Commission Employees',
        compute='_compute_commission_employee_partners',
        help='Work-contact partners of employees who have a commission scheme. '
             'Used to restrict the Vendor field to commission employees on the '
             'commission payment form.',
    )

    @api.depends_context('company')
    def _compute_commission_employee_partners(self):
        # Employees that have a commission scheme (any year) in the allowed
        # companies, resolved to their work-contact partner.
        schemes = self.env['vpa.commission.scheme'].search([])
        partners = schemes.employee_id.work_contact_id
        for pay in self:
            pay.commission_employee_partner_ids = partners

    @api.depends('amount', 'commission_allocation_ids.amount', 'commission_year_id')
    def _compute_commission_allocation(self):
        for pay in self:
            allocated = sum(pay.commission_allocation_ids.mapped('amount'))
            pay.commission_allocated_amount = allocated
            # A full-year link consumes the whole payment.
            if pay.commission_year_id:
                pay.commission_unallocated_amount = 0.0
            else:
                pay.commission_unallocated_amount = pay.amount - allocated

    @api.constrains('commission_year_id')
    def _check_commission_year_vs_allocations(self):
        for pay in self:
            if pay.commission_year_id and pay.commission_allocation_ids:
                raise ValidationError(_(
                    'Payment %(payment)s has commission allocations. A payment '
                    'is either fully linked to one year (Commission Year) or '
                    'split via allocations — not both.',
                    payment=pay.display_name,
                ))

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
        if self.commission_year_id or self.commission_allocation_ids:
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

