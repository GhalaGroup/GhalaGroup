# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CommissionPayYearWizard(models.TransientModel):
    _name = 'vpa.commission.pay.year.wizard'
    _description = 'Pay Commission for a Year'

    scheme_year_id = fields.Many2one(
        'vpa.commission.scheme.year',
        string='Commission Year',
        required=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        related='scheme_year_id.employee_id',
        string='Employee',
    )
    year = fields.Selection(
        related='scheme_year_id.year',
        string='Year',
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='scheme_year_id.currency_id',
        string='Commission Currency',
    )
    company_id = fields.Many2one(
        'res.company',
        related='scheme_year_id.company_id',
    )

    # Info (read-only context for the user)
    amount_due_year = fields.Monetary(
        related='scheme_year_id.amount_due_year',
        string='Due for Year',
        currency_field='currency_id',
    )
    amount_paid_cash = fields.Monetary(
        related='scheme_year_id.amount_paid_cash',
        string='Already Paid',
        currency_field='currency_id',
    )
    outstanding_cash = fields.Monetary(
        related='scheme_year_id.outstanding_cash',
        string='Outstanding',
        currency_field='currency_id',
    )

    # Payment inputs
    amount = fields.Monetary(
        string='Amount to Settle',
        currency_field='currency_id',
        required=True,
        help='Portion of the outstanding commission being settled, '
             'in the commission currency.',
    )
    payment_currency_id = fields.Many2one(
        'res.currency',
        string='Pay In',
        required=True,
        help='Currency the payment will actually be made in. '
             'The payment amount converts using the rate at the payment date.',
    )
    payment_amount = fields.Monetary(
        string='Payment Amount',
        currency_field='payment_currency_id',
        help='Actual amount to pay, in the payment currency. '
             'Edit either this or the Amount to Settle — they stay in sync.',
    )
    rate_info = fields.Char(
        string='Exchange Rate',
        compute='_compute_rate_info',
        help='Conversion rate applied at the payment date '
             '(nearest older rate is used if none exists on that exact date).',
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Payment Journal',
        domain="[('type', 'in', ('bank', 'cash')), ('company_id', '=', company_id), "
               "'|', ('currency_id', '=', payment_currency_id), ('currency_id', '=', False)]",
        required=True,
    )
    payment_date = fields.Date(
        string='Payment Date',
        default=fields.Date.today,
        required=True,
    )
    memo = fields.Char(
        string='Memo',
    )
    advance_payment = fields.Boolean(
        string='Advance Payment',
        help='Pay beyond what is currently payable (guarantee + confirmed '
             'commission) — e.g. an advance on a year with no minimum guarantee '
             'or before commissions are approved. The payment is linked to the '
             'year and applies against future bills.',
    )
    create_transaction = fields.Boolean(
        string='Add to Journal Transactions',
        compute='_compute_create_transaction',
        store=True,
        readonly=False,
        help='Also create the transaction in the journal\'s transaction list so the '
             'user only has to reconcile it once the money movement is confirmed. '
             'Recommended for cash/transit journals. Leave OFF for bank journals '
             'with statement import/sync — the imported statement would duplicate it.',
    )

    @api.depends('journal_id')
    def _compute_create_transaction(self):
        for wiz in self:
            wiz.create_transaction = wiz.journal_id.type == 'cash'

    # Rounding: pay a clean amount and write off the small remainder
    payment_difference = fields.Monetary(
        string='Difference',
        currency_field='currency_id',
        compute='_compute_payment_difference',
        help='Outstanding remaining after this payment.',
    )
    writeoff_difference = fields.Boolean(
        string='Write Off the Difference',
        help='Close the remaining difference with a rounding write-off entry, '
             'so nothing stays outstanding.',
    )
    writeoff_account_id = fields.Many2one(
        'account.account',
        string='Write-off Account',
        help='Account the rounding difference is booked to.',
    )

    @api.depends('amount', 'scheme_year_id')
    def _compute_payment_difference(self):
        for wiz in self:
            wiz.payment_difference = (wiz.scheme_year_id.outstanding_cash or 0.0) - wiz.amount

    # ------------------------------------------------------------------
    # Currency conversion helpers
    # ------------------------------------------------------------------
    def _convert(self, amount, from_cur, to_cur):
        """Convert between currencies at the payment date (scheme company rates)."""
        if not from_cur or not to_cur or from_cur == to_cur:
            return amount
        return from_cur._convert(
            amount, to_cur,
            self.company_id or self.env.company,
            self.payment_date or fields.Date.today(),
        )

    @api.depends('payment_currency_id', 'currency_id', 'payment_date', 'company_id')
    def _compute_rate_info(self):
        for wiz in self:
            pc, cc = wiz.payment_currency_id, wiz.currency_id
            if not pc or not cc or pc == cc:
                wiz.rate_info = False
                continue
            one_unit = wiz._convert(1.0, pc, cc)
            wiz.rate_info = _('1 %(pay)s = %(rate)s %(com)s (as of %(date)s)') % {
                'pay': pc.name,
                'rate': f'{one_unit:,.2f}',
                'com': cc.name,
                'date': wiz.payment_date or fields.Date.today(),
            }

    @api.onchange('amount', 'payment_currency_id', 'payment_date')
    def _onchange_amount(self):
        """Settle amount / currency / date changed -> refresh the payment amount."""
        if self.env.context.get('_skip_pay_sync'):
            return
        self.with_context(_skip_pay_sync=True).payment_amount = self._convert(
            self.amount, self.currency_id, self.payment_currency_id
        )
        # Re-pick a compatible journal if the current one clashes with the currency
        if self.journal_id and self.journal_id.currency_id and \
                self.journal_id.currency_id != self.payment_currency_id:
            self.journal_id = self._find_journal()

    @api.onchange('payment_amount')
    def _onchange_payment_amount(self):
        """Payment amount typed directly -> back-fill the settle amount."""
        if self.env.context.get('_skip_pay_sync'):
            return
        self.with_context(_skip_pay_sync=True).amount = self._convert(
            self.payment_amount, self.payment_currency_id, self.currency_id
        )

    def _find_journal(self, company=None, currency=None):
        """Bank/cash journal matching the payment currency (or currency-less)."""
        company = company or self.company_id
        currency = currency or self.payment_currency_id
        Journal = self.env['account.journal']
        return Journal.search([
            ('type', 'in', ('bank', 'cash')),
            ('company_id', '=', company.id),
            ('currency_id', '=', currency.id),
        ], limit=1) or Journal.search([
            ('type', 'in', ('bank', 'cash')),
            ('company_id', '=', company.id),
            ('currency_id', '=', False),
        ], limit=1)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        year_id = res.get('scheme_year_id') or self.env.context.get('default_scheme_year_id')
        # Only trust active_id when it really is a scheme year record
        if not year_id and self.env.context.get('active_model') == 'vpa.commission.scheme.year':
            year_id = self.env.context.get('active_id')
        if year_id:
            sy = self.env['vpa.commission.scheme.year'].browse(year_id)
            res['scheme_year_id'] = sy.id
            res['amount'] = max(0.0, sy.outstanding_cash)
            res['payment_currency_id'] = sy.currency_id.id
            res['payment_amount'] = res['amount']
            res['memo'] = _('Commission %s - %s', sy.year, sy.employee_id.name)
            journal = self._find_journal(company=sy.company_id, currency=sy.currency_id)
            if journal:
                res['journal_id'] = journal.id
            wo_account = sy.effective_expense_account_id or sy.scheme_id.expense_account_id
            if wo_account:
                res['writeoff_account_id'] = wo_account.id
        return res

    def action_pay(self):
        self.ensure_one()
        sy = self.scheme_year_id
        if self.payment_amount <= 0 or self.amount <= 0:
            raise UserError(_('The payment amount must be greater than zero.'))

        # Hard ceiling: only the guarantee and CONFIRMED commission are payable.
        # Tolerance: one rounding unit of the payment currency (a USD cent is
        # ~28.5 TZS), so cross-currency rounding can't block the final payment.
        ceiling = max(sy.minimum_amount, sy.confirmed_earned) - sy.amount_paid_cash
        tolerance = 0.01
        if self.payment_currency_id and self.payment_currency_id != self.currency_id:
            tolerance = max(tolerance, self._convert(
                self.payment_currency_id.rounding,
                self.payment_currency_id, self.currency_id))
        if self.writeoff_difference:
            # Rounding allowance: paying a clean figure slightly above the exact
            # outstanding is fine — the overage is written off as rounding.
            tolerance = max(tolerance, 10000.0)
        if self.advance_payment:
            # Explicit manager decision: pay ahead of guarantee/approvals.
            # The payment is year-linked and applies against future bills.
            tolerance = float('inf')
        if self.amount > ceiling + tolerance:
            raise UserError(_(
                'This payment (%(amt)s) exceeds what is payable for %(year)s.\n\n'
                'Payable = max(guarantee %(guar)s, confirmed commission %(conf)s) '
                '− already paid %(paid)s = %(ceil)s.\n\n'
                '%(pending)d commission line(s) are still awaiting confirmation — '
                'confirm them first, or tick "Advance Payment" to deliberately '
                'pay ahead.') % {
                    'amt': f'{self.amount:,.2f}',
                    'year': sy.year,
                    'guar': f'{sy.minimum_amount:,.2f}',
                    'conf': f'{sy.confirmed_earned:,.2f}',
                    'paid': f'{sy.amount_paid_cash:,.2f}',
                    'ceil': f'{max(0.0, ceiling):,.2f}',
                    'pending': sy.pending_count,
                })
        if self.journal_id.currency_id and self.journal_id.currency_id != self.payment_currency_id:
            raise UserError(_(
                'Journal "%s" is a %s journal and cannot pay in %s.',
                self.journal_id.name, self.journal_id.currency_id.name,
                self.payment_currency_id.name,
            ))

        partner = sy.employee_id.work_contact_id
        if not partner:
            raise UserError(_(
                'Employee "%s" has no work contact set. '
                'Please configure the work contact on the employee form first.',
                sy.employee_id.name,
            ))

        payment = self.env['account.payment'].create({
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'partner_id': partner.id,
            'amount': self.payment_amount,
            'currency_id': self.payment_currency_id.id,
            'journal_id': self.journal_id.id,
            'date': self.payment_date,
            'memo': self.memo,
            'commission_year_id': sy.id,
        })
        payment.action_post()

        # Match the payment against the year's open posted bills (oldest first)
        # so the employee's payable ledger stays clean automatically.
        self._auto_reconcile_with_bills(payment, sy)

        # Rounding write-off: close the small remainder so nothing stays open.
        if self.writeoff_difference:
            self._create_writeoff(sy, partner, payment)

        # Optionally pre-create the journal transaction so the user only has to
        # reconcile it once the money movement is confirmed.
        if self.create_transaction:
            self._create_journal_transaction(payment, partner)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Commission Payment'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            'res_id': payment.id,
            'target': 'current',
        }

    def _auto_reconcile_with_bills(self, payment, scheme_year):
        """Reconcile the payment's payable line against the year's open bills."""
        pay_lines = payment.move_id.line_ids.filtered(
            lambda l: l.account_id.account_type == 'liability_payable' and not l.reconciled
        ) if payment.move_id else self.env['account.move.line']
        if not pay_lines:
            return
        bill_lines = scheme_year.bill_ids.filtered(
            lambda b: b.state == 'posted' and b.move_type == 'in_invoice'
        ).line_ids.filtered(
            lambda l: l.account_id.account_type == 'liability_payable'
            and not l.reconciled and l.amount_residual
        ).sorted('date')
        if bill_lines:
            (pay_lines | bill_lines).reconcile()

    def _create_writeoff(self, scheme_year, partner, payment):
        """Write off the rounding difference in either direction.

        Underpaid: the bills' small open remainder is cleared (Dr Payable /
        Cr write-off account). Overpaid: the payment's small unapplied surplus
        is booked as rounding expense (Dr write-off account / Cr Payable).
        """
        if not self.writeoff_account_id:
            raise UserError(_('Please select a write-off account.'))

        # Underpaid? bills still have an open payable remainder.
        open_lines = scheme_year.bill_ids.filtered(
            lambda b: b.state == 'posted' and b.move_type == 'in_invoice'
        ).line_ids.filtered(
            lambda l: l.account_id.account_type == 'liability_payable'
            and not l.reconciled and l.amount_residual
        )
        residual = -sum(open_lines.mapped('amount_residual'))  # payable residual is negative
        if residual > 0:
            entry = self._make_writeoff_entry(
                scheme_year, partner, open_lines[0].account_id, residual, overpay=False)
            wo_line = entry.line_ids.filtered(
                lambda l: l.account_id.account_type == 'liability_payable')
            (wo_line | open_lines).reconcile()
            return

        # Overpaid? the payment carries an unapplied surplus.
        pay_lines = payment.move_id.line_ids.filtered(
            lambda l: l.account_id.account_type == 'liability_payable'
            and not l.reconciled and l.amount_residual
        ) if payment.move_id else self.env['account.move.line']
        surplus = sum(pay_lines.mapped('amount_residual'))  # payment residual is positive
        if surplus > 0:
            entry = self._make_writeoff_entry(
                scheme_year, partner, pay_lines[0].account_id, surplus, overpay=True)
            wo_line = entry.line_ids.filtered(
                lambda l: l.account_id.account_type == 'liability_payable')
            (wo_line | pay_lines).reconcile()

    def _make_writeoff_entry(self, scheme_year, partner, payable_account, amount, overpay):
        journal = self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', scheme_year.company_id.id),
        ], limit=1)
        if not journal:
            raise UserError(_('No miscellaneous journal found for %s.',
                              scheme_year.company_id.name))
        ref = _('Commission rounding write-off - %s %s',
                scheme_year.employee_id.name, scheme_year.year)
        ap_vals = {'name': ref, 'account_id': payable_account.id, 'partner_id': partner.id}
        wo_vals = {'name': ref, 'account_id': self.writeoff_account_id.id}
        if overpay:
            ap_vals.update(debit=0.0, credit=amount)   # surplus stays with the employee
            wo_vals.update(debit=amount, credit=0.0)   # booked as rounding expense
        else:
            ap_vals.update(debit=amount, credit=0.0)   # clear the open remainder
            wo_vals.update(debit=0.0, credit=amount)   # expense reduced by the remainder
        entry = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': journal.id,
            'date': self.payment_date,
            'ref': ref,
            'commission_year_id': scheme_year.id,
            'commission_writeoff': True,
            'line_ids': [(0, 0, ap_vals), (0, 0, wo_vals)],
        })
        entry.action_post()
        return entry

    def _create_journal_transaction(self, payment, partner):
        """Create the (unreconciled) statement line mirroring this outbound payment."""
        journal = self.journal_id
        label = self.memo or payment.name
        vals = {
            'journal_id': journal.id,
            'date': self.payment_date,
            'payment_ref': label,
            'partner_id': partner.id,
        }
        if not journal.currency_id or journal.currency_id == self.payment_currency_id:
            # Journal denominated in the payment currency (or company currency journal
            # paid in company currency): statement amount is simply the payment amount.
            vals['amount'] = -self.payment_amount
        else:
            # Currency-less journal paid in a foreign currency: statement amount is in
            # company currency, with the foreign amount carried alongside.
            company = self.company_id or self.env.company
            vals['amount'] = -self.payment_currency_id._convert(
                self.payment_amount, company.currency_id, company, self.payment_date,
            )
            vals['foreign_currency_id'] = self.payment_currency_id.id
            vals['amount_currency'] = -self.payment_amount
        # sudo: statement-line creation needs full accounting rights, which a
        # commission manager (Billing via implied group) doesn't have. The scope
        # is safe: wizard is manager-only by ACL, and the journal is restricted
        # to the scheme's company by the field domain.
        return self.env['account.bank.statement.line'].sudo().create(vals)
