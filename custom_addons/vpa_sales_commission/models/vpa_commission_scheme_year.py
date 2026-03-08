# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class VpaCommissionSchemeYear(models.Model):
    _name = 'vpa.commission.scheme.year'
    _description = 'Commission Scheme Year'
    _order = 'year desc'
    _rec_name = 'display_name'

    scheme_id = fields.Many2one(
        'vpa.commission.scheme',
        string='Commission Scheme',
        required=True,
        ondelete='cascade',
        index=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        related='scheme_id.employee_id',
        store=True,
        index=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='scheme_id.company_id',
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='scheme_id.currency_id',
        store=True,
    )

    @api.model
    def _get_year_selection(self):
        current_year = fields.Date.today().year
        return [(str(y), str(y)) for y in range(2020, current_year + 3)]

    year = fields.Selection(
        selection='_get_year_selection',
        string='Year',
        required=True,
        index=True,
    )
    display_name = fields.Char(
        string='Name',
        compute='_compute_display_name',
        store=True,
    )
    production_rate = fields.Float(
        string='Rate (%)',
        digits=(5, 2),
        help='Commission percentage for this year',
    )
    minimum_amount = fields.Monetary(
        string='Min. Guarantee',
        currency_field='currency_id',
        help='Annual minimum commission guarantee for this year',
    )
    minimum_amount_usd = fields.Float(
        string='USD Equivalent',
        digits=(12, 2),
        help='Enter the USD amount to auto-convert to the scheme currency using current rates',
    )

    @api.onchange('minimum_amount_usd', 'year')
    def _onchange_minimum_amount_usd(self):
        if not self.minimum_amount_usd or not self.year:
            return
        usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if not usd or not self.currency_id or self.currency_id == usd:
            return
        import datetime
        # Use Dec 31 of the selected year; cap at today for future years
        rate_date = datetime.date(int(self.year), 12, 31)
        today = fields.Date.today()
        if rate_date > today:
            rate_date = today
        converted = usd._convert(
            self.minimum_amount_usd,
            self.currency_id,
            self.company_id or self.env.company,
            rate_date,
        )
        self.minimum_amount = converted
    expense_account_id = fields.Many2one(
        'account.account',
        string='Expense Account',
        domain="[('account_type', 'in', ('expense', 'expense_direct_cost'))]",
        help='Debit account for commission expense journal entries. Overrides scheme default.',
    )
    notes = fields.Text(string='Notes')

    # Year state
    state = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed'),
    ], string='State', default='open', required=True)

    # Computed totals from commission lines
    total_earned = fields.Monetary(
        string='Total Earned',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
    )
    total_paid = fields.Monetary(
        string='Total Paid',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
    )
    total_pending = fields.Monetary(
        string='Pending',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
    )
    shortfall = fields.Monetary(
        string='Shortfall',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
        help='How much below the minimum guarantee',
    )
    outstanding = fields.Monetary(
        string='Outstanding',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
        help='Earned but not yet paid',
    )

    # Bills
    bill_ids = fields.One2many(
        'account.move',
        'commission_year_id',
        string='Vendor Bills',
        domain=[('move_type', '=', 'in_invoice')],
    )
    bill_count = fields.Integer(
        string='Bills',
        compute='_compute_bill_count',
    )

    # Advance tracking: how much of the minimum guarantee has been consumed by monthly bills
    advance_consumed = fields.Monetary(
        string='Advance Consumed',
        currency_field='currency_id',
        compute='_compute_advance',
        store=True,
        help='Total MO commission billed so far — deducted from the minimum guarantee advance.',
    )
    advance_remaining = fields.Monetary(
        string='Advance Remaining',
        currency_field='currency_id',
        compute='_compute_advance',
        store=True,
        help='Portion of the minimum guarantee advance not yet consumed by MO commissions.',
    )
    payable_to_employee = fields.Monetary(
        string='Payable to Employee',
        currency_field='currency_id',
        compute='_compute_advance',
        store=True,
        help='Amount owed to employee above the minimum guarantee advance (only positive once advance is fully consumed).',
    )

    _year_uniq = models.Constraint(
        'unique(scheme_id, year)',
        'A year configuration already exists for this employee and year!',
    )

    @api.depends('employee_id', 'year')
    def _compute_display_name(self):
        for rec in self:
            if rec.employee_id and rec.year:
                rec.display_name = f"{rec.employee_id.name} - {rec.year}"
            else:
                rec.display_name = _('New Year')

    @api.depends(
        'scheme_id.commission_line_ids',
        'scheme_id.commission_line_ids.amount',
        'scheme_id.commission_line_ids.state',
        'scheme_id.commission_line_ids.date_year',
        'minimum_amount',
        'year',
    )
    def _compute_totals(self):
        for rec in self:
            lines = rec.scheme_id.commission_line_ids.filtered(
                lambda l: l.date_year == rec.year and l.state != 'cancelled'
            )
            rec.total_earned = sum(lines.mapped('amount'))
            rec.total_paid = sum(lines.filtered(lambda l: l.state == 'paid').mapped('amount'))
            rec.total_pending = sum(lines.filtered(lambda l: l.state == 'pending').mapped('amount'))
            rec.shortfall = max(0.0, rec.minimum_amount - rec.total_earned)
            rec.outstanding = max(0.0, rec.total_earned - rec.total_paid)

    @api.depends('bill_ids')
    def _compute_bill_count(self):
        for rec in self:
            rec.bill_count = len(rec.bill_ids)

    @api.depends('bill_ids', 'bill_ids.commission_month', 'bill_ids.amount_total', 'minimum_amount')
    def _compute_advance(self):
        for rec in self:
            # Monthly bills have commission_month set; the base guarantee bill does not
            monthly_bills = rec.bill_ids.filtered(
                lambda b: b.commission_month and b.move_type == 'in_invoice'
            )
            consumed = sum(monthly_bills.mapped('amount_total'))
            rec.advance_consumed = consumed
            rec.advance_remaining = max(0.0, rec.minimum_amount - consumed)
            rec.payable_to_employee = max(0.0, consumed - rec.minimum_amount)

    @api.constrains('production_rate')
    def _check_rate(self):
        for rec in self:
            if rec.production_rate < 0 or rec.production_rate > 100:
                raise ValidationError(_('Commission rate must be between 0 and 100%.'))

    def action_close_year(self):
        """Close the year: lock all commission lines."""
        self.ensure_one()
        if self.state == 'closed':
            raise UserError(_('This year is already closed.'))

        # Check for unpaid lines
        lines = self.scheme_id.commission_line_ids.filtered(
            lambda l: l.date_year == self.year and l.state not in ('paid', 'cancelled')
        )
        if lines:
            # Return a confirmation wizard
            return {
                'type': 'ir.actions.act_window',
                'name': _('Close Year - Unpaid Lines'),
                'res_model': 'vpa.commission.close.year.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_scheme_year_id': self.id,
                    'default_unpaid_count': len(lines),
                    'default_unpaid_amount': sum(lines.mapped('amount')),
                },
            }
        self._do_close_year()

    def _do_close_year(self):
        """Actually close the year — lock lines and set state."""
        self.ensure_one()
        # Lock all commission lines for this year
        lines = self.scheme_id.commission_line_ids.filtered(
            lambda l: l.date_year == self.year and l.state != 'cancelled'
        )
        lines.write({'year_locked': True})
        self.write({'state': 'closed'})

    def action_reopen_year(self):
        """Reopen a closed year (manager action)."""
        self.ensure_one()
        lines = self.scheme_id.commission_line_ids.filtered(
            lambda l: l.date_year == self.year
        )
        lines.write({'year_locked': False})
        self.write({'state': 'open'})

    def action_view_commission_lines(self):
        """Open commission lines for this year."""
        self.ensure_one()
        return {
            'name': _('Commission Lines - %s (%s)', self.employee_id.name, self.year),
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.commission.line',
            'view_mode': 'list,pivot,graph,form',
            'domain': [
                ('scheme_id', '=', self.scheme_id.id),
                ('date_year', '=', self.year),
                ('state', '!=', 'cancelled'),
            ],
        }

    def action_view_bills(self):
        """Open vendor bills for this year."""
        self.ensure_one()
        return {
            'name': _('Bills - %s (%s)', self.employee_id.name, self.year),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('commission_year_id', '=', self.id)],
        }

    def action_generate_bill(self):
        """Open bill generation wizard for this year."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generate Commission Bill'),
            'res_model': 'vpa.commission.bill.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_scheme_id': self.scheme_id.id,
                'default_year': self.year,
            },
        }


class VpaCommissionCloseYearWizard(models.TransientModel):
    _name = 'vpa.commission.close.year.wizard'
    _description = 'Close Year Confirmation'

    scheme_year_id = fields.Many2one(
        'vpa.commission.scheme.year',
        string='Scheme Year',
        required=True,
    )
    unpaid_count = fields.Integer(string='Unpaid Lines', readonly=True)
    unpaid_amount = fields.Float(string='Unpaid Amount', digits=(12, 2), readonly=True)
    currency_id = fields.Many2one(
        'res.currency',
        related='scheme_year_id.currency_id',
    )

    def action_confirm_close(self):
        """Confirm closing the year despite unpaid lines."""
        self.ensure_one()
        self.scheme_year_id._do_close_year()
        return {'type': 'ir.actions.act_window_close'}
