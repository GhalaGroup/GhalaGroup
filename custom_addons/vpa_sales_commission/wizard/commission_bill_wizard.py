# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

import calendar
import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang


class CommissionBillWizard(models.TransientModel):
    _name = 'vpa.commission.bill.wizard'
    _description = 'Commission Bill Generation Wizard'

    scheme_id = fields.Many2one(
        'vpa.commission.scheme',
        string='Commission Scheme',
        required=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        related='scheme_id.employee_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='scheme_id.currency_id',
    )

    bill_type = fields.Selection([
        ('monthly', 'Monthly Commission'),
        ('base', 'Base / Minimum Guarantee'),
    ], string='Bill Type', default='monthly', required=True)
    include_mo_lines = fields.Boolean(
        string='Include MO Commission Lines',
        default=False,
        help='Also include all unbilled MO commission lines for this year in the guarantee bill',
    )

    @api.model
    def _get_year_selection(self):
        current_year = fields.Date.today().year
        return [(str(y), str(y)) for y in range(2020, current_year + 3)]

    @api.model
    def _get_month_selection(self):
        return [
            ('01', 'January'), ('02', 'February'), ('03', 'March'),
            ('04', 'April'), ('05', 'May'), ('06', 'June'),
            ('07', 'July'), ('08', 'August'), ('09', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December'),
        ]

    year = fields.Selection(
        selection='_get_year_selection',
        string='Year',
        required=True,
        default=lambda self: str(fields.Date.today().year),
    )
    month = fields.Selection(
        selection='_get_month_selection',
        string='Month',
    )

    # Base bill preview
    guarantee_amount = fields.Monetary(
        string='Guarantee Amount',
        currency_field='currency_id',
        compute='_compute_guarantee_amount',
    )
    guarantee_line_description = fields.Char(
        string='Bill Line Description',
        compute='_compute_guarantee_amount',
    )
    guarantee_deferred_note = fields.Text(
        string='Deferred Note',
        compute='_compute_guarantee_amount',
    )

    @api.depends('scheme_id', 'year')
    def _compute_guarantee_amount(self):
        month_names = [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
        ]
        for wizard in self:
            if wizard.scheme_id and wizard.year:
                scheme_year = wizard.env['vpa.commission.scheme.year'].search([
                    ('scheme_id', '=', wizard.scheme_id.id),
                    ('year', '=', wizard.year),
                ], limit=1)
                if scheme_year:
                    wizard.guarantee_amount = scheme_year.minimum_amount
                    wizard.guarantee_line_description = (
                        f"Minimum Guarantee Commission - {wizard.scheme_id.employee_id.name} {wizard.year}"
                    )
                    # Build monthly breakdown note
                    if scheme_year.minimum_amount:
                        monthly = scheme_year.minimum_amount / 12
                        symbol = wizard.currency_id.symbol or wizard.currency_id.name or ''
                        monthly_str = f"{symbol} {monthly:,.2f}"
                        year_int = int(wizard.year)
                        lines = ["Deferred: Jan 1 – Dec 31 (spread equally over 12 months)"]
                        for m_idx, m_name in enumerate(month_names, start=1):
                            last_day = calendar.monthrange(year_int, m_idx)[1]
                            lines.append(f"{m_name} {last_day}, {wizard.year}: {monthly_str}")
                        wizard.guarantee_deferred_note = '\n'.join(lines)
                    else:
                        wizard.guarantee_deferred_note = "Deferred: Jan 1 – Dec 31 (spread equally over 12 months)"
                else:
                    wizard.guarantee_amount = 0.0
                    wizard.guarantee_line_description = False
                    wizard.guarantee_deferred_note = False
            else:
                wizard.guarantee_amount = 0.0
                wizard.guarantee_line_description = False
                wizard.guarantee_deferred_note = False

    # Lines to bill (auto-populated)
    line_ids = fields.Many2many(
        'vpa.commission.line',
        'vpa_commission_bill_wizard_line_rel',
        'wizard_id',
        'line_id',
        string='Commission Lines',
    )
    line_count = fields.Integer(
        string='Lines',
        compute='_compute_totals',
    )
    total_amount = fields.Monetary(
        string='Total Amount',
        currency_field='currency_id',
        compute='_compute_totals',
    )

    # Bill settings
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        domain="[('type', '=', 'purchase')]",
        required=True,
    )
    expense_account_id = fields.Many2one(
        'account.account',
        string='Expense Account',
        domain="[('account_type', 'in', ('expense', 'expense_direct_cost'))]",
        required=True,
    )
    bill_date = fields.Date(
        string='Bill Date',
        required=True,
    )

    # Advance status (computed from scheme year)
    advance_remaining = fields.Monetary(
        string='Advance Remaining',
        currency_field='currency_id',
        compute='_compute_advance_status',
    )
    advance_status = fields.Selection([
        ('covered', 'Fully Covered by Advance'),
        ('partial', 'Partially Covered by Advance'),
        ('exceeded', 'Advance Fully Consumed — Payable to Employee'),
        ('no_advance', 'No Advance Set'),
    ], string='Advance Status', compute='_compute_advance_status')

    @api.depends('scheme_id', 'year', 'total_amount')
    def _compute_advance_status(self):
        for wizard in self:
            if not wizard.scheme_id or not wizard.year:
                wizard.advance_remaining = 0.0
                wizard.advance_status = 'no_advance'
                continue
            scheme_year = wizard.env['vpa.commission.scheme.year'].search([
                ('scheme_id', '=', wizard.scheme_id.id),
                ('year', '=', wizard.year),
            ], limit=1)
            if not scheme_year or not scheme_year.minimum_amount:
                wizard.advance_remaining = 0.0
                wizard.advance_status = 'no_advance'
                continue
            wizard.advance_remaining = scheme_year.advance_remaining
            if scheme_year.advance_remaining <= 0:
                wizard.advance_status = 'exceeded'
            elif wizard.total_amount <= scheme_year.advance_remaining:
                wizard.advance_status = 'covered'
            else:
                wizard.advance_status = 'partial'

    # Info about existing bills for this period
    existing_bill_ids = fields.Many2many(
        'account.move',
        'vpa_commission_bill_wizard_existing_rel',
        'wizard_id',
        'bill_id',
        string='Existing Bills for this Period',
        compute='_compute_existing_bills',
    )
    existing_bill_count = fields.Integer(
        string='Existing Bills',
        compute='_compute_existing_bills',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        today = fields.Date.today()

        # Try to detect year and month from the active commission lines
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            lines = self.env['vpa.commission.line'].browse(active_ids).filtered(
                lambda l: l.state != 'cancelled'
            )
            if lines:
                # Use the year from the lines (take the most common year)
                years = lines.mapped('date_year')
                detected_year = max(set(years), key=years.count) if years else str(today.year)
                # Use the month from the lines (take the most common month)
                months = [l.date.strftime('%m') for l in lines if l.date]
                detected_month = max(set(months), key=months.count) if months else today.strftime('%m')
                res['year'] = detected_year
                res['month'] = detected_month
                year_int = int(detected_year)
                month_int = int(detected_month)
                last_day = calendar.monthrange(year_int, month_int)[1]
                res['bill_date'] = datetime.date(year_int, month_int, last_day)

                # Also pre-load the unbilled lines for this period
                # (onchange won't fire on default_get, so we do it here)
                scheme = lines[0].scheme_id if lines else False
                if scheme:
                    month_prefix = f"{detected_year}-{detected_month}"
                    unbilled = self.env['vpa.commission.line'].search([
                        ('scheme_id', '=', scheme.id),
                        ('date_year', '=', detected_year),
                        ('date_month', '=', month_prefix),
                        ('bill_id', '=', False),
                        ('state', 'not in', ('cancelled',)),
                    ])
                    if unbilled:
                        res['line_ids'] = [(6, 0, unbilled.ids)]
                        res['scheme_id'] = scheme.id
                return res

        # Fallback: use today's date
        res['month'] = today.strftime('%m')
        last_day = calendar.monthrange(today.year, today.month)[1]
        res['bill_date'] = datetime.date(today.year, today.month, last_day)
        return res

    def _get_last_day_of_period(self):
        """Return last day of selected year/month, or last day of year if no month."""
        if self.year and self.month:
            y, m = int(self.year), int(self.month)
            last_day = calendar.monthrange(y, m)[1]
            return datetime.date(y, m, last_day)
        elif self.year:
            return datetime.date(int(self.year), 12, 31)
        return fields.Date.today()

    @api.onchange('scheme_id', 'year', 'month', 'bill_type')
    def _onchange_scheme_year(self):
        """Load expense account, journal, and bill date from scheme/period."""
        if self.scheme_id and self.year:
            account = self.scheme_id._get_expense_account_for_year(self.year)
            if account:
                self.expense_account_id = account
            # Set journal matching scheme currency
            currency = self.scheme_id.currency_id
            if currency:
                journal = self.env['account.journal'].search([
                    ('type', '=', 'purchase'),
                    ('currency_id', '=', currency.id),
                ], limit=1)
                if not journal:
                    # Fallback: journal with no specific currency (uses company currency)
                    journal = self.env['account.journal'].search([
                        ('type', '=', 'purchase'),
                        ('currency_id', '=', False),
                    ], limit=1)
                if journal:
                    self.journal_id = journal
        # Set bill date: Jan 1 for base/guarantee (so deferred spreads Jan-Dec), last day of month for monthly
        if self.year:
            if self.bill_type == 'base':
                self.bill_date = datetime.date(int(self.year), 1, 1)
            else:
                self.bill_date = self._get_last_day_of_period()

    @api.onchange('scheme_id', 'year', 'month', 'bill_type')
    def _onchange_load_lines(self):
        """Load unbilled commission lines for the selected period."""
        if not self.scheme_id or not self.year:
            self.line_ids = False
            return
        domain = [
            ('scheme_id', '=', self.scheme_id.id),
            ('date_year', '=', self.year),
            ('bill_id', '=', False),
            ('state', 'not in', ('cancelled',)),
        ]
        if self.bill_type == 'monthly' and self.month:
            month_prefix = f"{self.year}-{self.month}"
            domain.append(('date_month', '=', month_prefix))
        self.line_ids = self.env['vpa.commission.line'].search(domain)

    @api.depends('line_ids', 'line_ids.amount')
    def _compute_totals(self):
        for wizard in self:
            wizard.line_count = len(wizard.line_ids)
            wizard.total_amount = sum(wizard.line_ids.mapped('amount'))

    @api.depends('scheme_id', 'year', 'month', 'bill_type')
    def _compute_existing_bills(self):
        for wizard in self:
            if not wizard.scheme_id or not wizard.year:
                wizard.existing_bill_ids = False
                wizard.existing_bill_count = 0
                continue
            domain = [
                ('commission_year_id.scheme_id', '=', wizard.scheme_id.id),
                ('commission_year_id.year', '=', wizard.year),
                ('move_type', '=', 'in_invoice'),
            ]
            if wizard.bill_type == 'monthly' and wizard.month:
                domain.append(('commission_month', '=', wizard.month))
            bills = self.env['account.move'].search(domain)
            wizard.existing_bill_ids = bills
            wizard.existing_bill_count = len(bills)

    def _get_employee_partner(self):
        employee = self.scheme_id.employee_id
        partner = employee.work_contact_id
        if not partner:
            raise UserError(_(
                'Employee "%s" has no work contact set. '
                'Please configure the work contact on the employee form first.',
                employee.name,
            ))
        return partner

    def action_create_bill(self):
        self.ensure_one()
        if self.bill_type == 'base':
            return self._create_base_bill()
        return self._create_monthly_bill()

    def _create_monthly_bill(self):
        """Create a vendor bill for the selected monthly commission lines."""
        if not self.line_ids:
            raise UserError(_('No unbilled commission lines found for the selected period.'))

        partner = self._get_employee_partner()

        if not self.expense_account_id:
            raise UserError(_('Please select an expense account.'))

        scheme_year = self.env['vpa.commission.scheme.year'].search([
            ('scheme_id', '=', self.scheme_id.id),
            ('year', '=', self.year),
        ], limit=1)

        invoice_lines = []
        for cl in self.line_ids:
            mo_ref = cl.production_id.name if cl.production_id else cl.name
            description = f"{mo_ref} - {cl.date}"
            if cl.item_name:
                description = f"{mo_ref} | {cl.item_name} | {cl.date}"
            invoice_lines.append((0, 0, {
                'name': description,
                'quantity': 1.0,
                'price_unit': cl.amount,
                'account_id': self.expense_account_id.id,
            }))

        month_labels = dict(self._get_month_selection())
        period_label = f"{month_labels.get(self.month, self.month)} {self.year}" if self.month else self.year

        bill_vals = {
            'move_type': 'in_invoice',
            'partner_id': partner.id,
            'journal_id': self.journal_id.id,
            'invoice_date': self.bill_date,
            'ref': _('Commission %s - %s', self.scheme_id.employee_id.name, period_label),
            'invoice_line_ids': invoice_lines,
            'commission_month': self.month,
        }
        if scheme_year:
            bill_vals['commission_year_id'] = scheme_year.id

        bill = self.env['account.move'].create(bill_vals)
        self.line_ids.write({'bill_id': bill.id})

        # If advance is still available, mark lines as paid (settled by advance)
        if scheme_year and scheme_year.minimum_amount:
            advance_remaining_before = scheme_year.advance_remaining + sum(self.line_ids.mapped('amount'))
            if advance_remaining_before > 0:
                # At least partially covered — mark all covered lines as paid
                covered_amount = 0.0
                for line in self.line_ids:
                    if covered_amount + line.amount <= advance_remaining_before:
                        line.write({
                            'state': 'paid',
                            'paid_date': self.bill_date,
                            'paid_by': self.env.uid,
                        })
                        covered_amount += line.amount

        return {
            'type': 'ir.actions.act_window',
            'name': _('Commission Bill'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': bill.id,
            'target': 'current',
        }

    def _create_base_bill(self):
        """Create a single vendor bill for the minimum guarantee amount."""
        partner = self._get_employee_partner()

        if not self.expense_account_id:
            raise UserError(_('Please select an expense account.'))

        scheme_year = self.env['vpa.commission.scheme.year'].search([
            ('scheme_id', '=', self.scheme_id.id),
            ('year', '=', self.year),
        ], limit=1)

        if not scheme_year:
            raise UserError(_('No yearly configuration found for %s - %s.', self.scheme_id.name, self.year))

        if not scheme_year.minimum_amount:
            raise UserError(_('The minimum guarantee amount for %s is zero. Please configure it first.', self.year))

        employee_name = self.scheme_id.employee_id.name
        year_int = int(self.year)
        invoice_lines = [(0, 0, {
            'name': _('Minimum Guarantee Commission - %s %s', employee_name, self.year),
            'quantity': 1.0,
            'price_unit': scheme_year.minimum_amount,
            'account_id': self.expense_account_id.id,
        })]

        # Optionally include unbilled MO commission lines
        mo_lines_to_link = self.env['vpa.commission.line']
        if self.include_mo_lines:
            mo_lines_to_link = self.env['vpa.commission.line'].search([
                ('scheme_id', '=', self.scheme_id.id),
                ('date_year', '=', self.year),
                ('bill_id', '=', False),
                ('state', 'not in', ('cancelled',)),
            ])
            for cl in mo_lines_to_link:
                mo_ref = cl.production_id.name if cl.production_id else cl.name
                description = f"{mo_ref} - {cl.date}"
                if cl.item_name:
                    description = f"{mo_ref} | {cl.item_name} | {cl.date}"
                invoice_lines.append((0, 0, {
                    'name': description,
                    'quantity': 1.0,
                    'price_unit': cl.amount,
                    'account_id': self.expense_account_id.id,
                }))

        bill_vals = {
            'move_type': 'in_invoice',
            'partner_id': partner.id,
            'journal_id': self.journal_id.id,
            'invoice_date': self.bill_date,
            'ref': _('Base Commission Guarantee - %s %s', employee_name, self.year),
            'invoice_line_ids': invoice_lines,
            'commission_year_id': scheme_year.id,
        }

        bill = self.env['account.move'].create(bill_vals)
        if mo_lines_to_link:
            mo_lines_to_link.write({'bill_id': bill.id})

        # Create 12 monthly prepaid expense journal entries
        self._create_monthly_prepaid_entries(scheme_year, year_int, employee_name, bill)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Base Commission Bill'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': bill.id,
            'target': 'current',
        }

    def _create_monthly_prepaid_entries(self, scheme_year, year_int, employee_name, bill):
        """Create and post 12 monthly journal entries to spread the guarantee expense across the year."""
        company = self.env.company
        prepaid_account = company.deferred_expense_account_id
        if not prepaid_account:
            return
        prepaid_journal = company.deferred_expense_journal_id
        if not prepaid_journal:
            return

        monthly_amount = scheme_year.minimum_amount / 12
        currency = self.currency_id or company.currency_id

        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December',
        ]

        moves = self.env['account.move']
        for m_idx in range(1, 13):
            last_day = calendar.monthrange(year_int, m_idx)[1]
            entry_date = datetime.date(year_int, m_idx, last_day)
            month_label = month_names[m_idx - 1]
            ref = f"Commission Guarantee - {employee_name} {month_label} {year_int}"
            amount = currency.round(monthly_amount)

            move_vals = {
                'move_type': 'entry',
                'journal_id': prepaid_journal.id,
                'date': entry_date,
                'ref': ref,
                'line_ids': [
                    (0, 0, {
                        'name': ref,
                        'account_id': self.expense_account_id.id,
                        'debit': amount,
                        'credit': 0.0,
                    }),
                    (0, 0, {
                        'name': ref,
                        'account_id': prepaid_account.id,
                        'debit': 0.0,
                        'credit': amount,
                    }),
                ],
            }
            moves |= self.env['account.move'].create(move_vals)

        # Post all 12 entries at once
        moves.action_post()

        # Link entries to the bill via deferred_move_ids
        bill.write({'deferred_move_ids': [fields.Command.set(moves.ids)]})

        # Log a note on the bill linking to the prepaid entries
        bill.message_post(
            body=_(
                'Prepaid expense entries created and posted: %s monthly entries of %s each '
                '(Jan–Dec %s) in journal "%s".',
                12,
                formatLang(self.env, currency.round(monthly_amount), currency_obj=currency),
                year_int,
                prepaid_journal.name,
            )
        )
