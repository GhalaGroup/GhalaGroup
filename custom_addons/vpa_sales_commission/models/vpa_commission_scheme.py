# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class VpaCommissionScheme(models.Model):
    _name = 'vpa.commission.scheme'
    _description = 'Commission Scheme'
    _order = 'employee_id'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        index=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
    )

    # Commission type toggles
    production_commission = fields.Boolean(
        string='Production Commission',
        default=True,
        help='Enable commission based on cost of commissionable raw materials consumed in Manufacturing Orders',
    )
    sales_commission = fields.Boolean(
        string='Sales Commission',
        default=False,
        help='Enable commission based on Sales Orders (Phase 2)',
    )

    # Commission rates - separate for Production and Sales
    production_rate = fields.Float(
        string='Production Rate (%)',
        digits=(5, 2),
        help='Percentage of commissionable raw material cost (e.g., 20.0 for 20%)',
    )
    sales_rate = fields.Float(
        string='Sales Rate (%)',
        digits=(5, 2),
        help='Commission rate for Sales Orders (e.g., 15.0 for 15%) - Phase 2',
    )

    # MO Filter fields
    apply_to = fields.Selection([
        ('all', 'All Manufacturing Orders'),
        ('workcenter', 'Specific Workcenters'),
        ('product_category', 'Product Categories'),
        ('specific_products', 'Specific Products'),
    ], string='Apply To', default='all', required=True,
        help='Define which Manufacturing Orders this scheme applies to')
    workcenter_ids = fields.Many2many(
        'mrp.workcenter',
        'vpa_commission_scheme_workcenter_rel',
        'scheme_id',
        'workcenter_id',
        string='Workcenters',
    )
    product_category_ids = fields.Many2many(
        'product.category',
        'vpa_commission_scheme_category_rel',
        'scheme_id',
        'category_id',
        string='Product Categories',
    )
    product_ids = fields.Many2many(
        'product.product',
        'vpa_commission_scheme_product_rel',
        'scheme_id',
        'product_id',
        string='Products',
    )

    # Default expense account (can be overridden per year)
    expense_account_id = fields.Many2one(
        'account.account',
        string='Expense Account',
        domain="[('account_type', 'in', ('expense', 'expense_direct_cost'))]",
        help='Default debit account for commission expense journal entries.',
    )

    # Related commission lines
    commission_line_ids = fields.One2many(
        'vpa.commission.line',
        'scheme_id',
        string='Commission Lines',
    )

    # Yearly rate/guarantee configuration
    year_ids = fields.One2many(
        'vpa.commission.scheme.year',
        'scheme_id',
        string='Yearly Configuration',
    )
    year_count = fields.Integer(
        string='Years',
        compute='_compute_year_count',
    )

    # Computed fields for dashboard/reporting
    total_commission = fields.Float(
        string='Total Commission',
        compute='_compute_totals',
        store=True,
    )
    total_pending = fields.Float(
        string='Pending Commission',
        compute='_compute_totals',
        store=True,
    )
    total_confirmed = fields.Float(
        string='Confirmed Commission',
        compute='_compute_totals',
        store=True,
    )

    _employee_uniq = models.Constraint(
        'unique(employee_id, company_id)',
        'A commission scheme already exists for this employee!',
    )

    @api.depends('employee_id')
    def _compute_name(self):
        for scheme in self:
            if scheme.employee_id:
                scheme.name = scheme.employee_id.name
            else:
                scheme.name = _('New Scheme')

    @api.depends('commission_line_ids', 'commission_line_ids.amount', 'commission_line_ids.state')
    def _compute_totals(self):
        for scheme in self:
            lines = scheme.commission_line_ids.filtered(lambda l: l.state != 'cancelled')
            scheme.total_commission = sum(lines.mapped('amount'))
            scheme.total_pending = sum(lines.filtered(lambda l: l.state == 'pending').mapped('amount'))
            scheme.total_confirmed = sum(lines.filtered(lambda l: l.state in ('confirmed', 'paid')).mapped('amount'))

    @api.constrains('production_rate', 'sales_rate')
    def _check_commission_rates(self):
        for scheme in self:
            if scheme.production_rate < 0 or scheme.production_rate > 100:
                raise ValidationError(_('Production commission rate must be between 0 and 100%.'))
            if scheme.sales_rate < 0 or scheme.sales_rate > 100:
                raise ValidationError(_('Sales commission rate must be between 0 and 100%.'))

    @api.constrains('apply_to', 'workcenter_ids', 'product_category_ids', 'product_ids')
    def _check_filter_fields(self):
        for scheme in self:
            if scheme.apply_to == 'workcenter' and not scheme.workcenter_ids:
                raise ValidationError(_('Please select at least one workcenter.'))
            if scheme.apply_to == 'product_category' and not scheme.product_category_ids:
                raise ValidationError(_('Please select at least one product category.'))
            if scheme.apply_to == 'specific_products' and not scheme.product_ids:
                raise ValidationError(_('Please select at least one product.'))

    def _applies_to_production(self, production):
        """Check if this scheme applies to a given manufacturing order."""
        self.ensure_one()
        if self.apply_to == 'all':
            return True
        elif self.apply_to == 'workcenter':
            # Check if any of the MO's workorders use our workcenters
            mo_workcenters = production.workorder_ids.mapped('workcenter_id')
            return bool(mo_workcenters & self.workcenter_ids)
        elif self.apply_to == 'product_category':
            return production.product_id.categ_id in self.product_category_ids
        elif self.apply_to == 'specific_products':
            return production.product_id in self.product_ids
        return False

    @api.depends('year_ids')
    def _compute_year_count(self):
        for scheme in self:
            scheme.year_count = len(scheme.year_ids)

    def _get_rate_for_year(self, year_str):
        """Return the commission rate for a given year. Falls back to production_rate."""
        self.ensure_one()
        year_line = self.year_ids.filtered(lambda y: y.year == year_str)
        if year_line and year_line[0].production_rate:
            return year_line[0].production_rate
        return self.production_rate

    def _get_minimum_for_year(self, year_str):
        """Return the minimum guarantee amount for a given year."""
        self.ensure_one()
        year_line = self.year_ids.filtered(lambda y: y.year == year_str)
        if year_line:
            return year_line[0].minimum_amount
        return 0.0

    def _get_expense_account_for_year(self, year_str):
        """Return the expense account for a given year. Falls back to scheme default."""
        self.ensure_one()
        year_line = self.year_ids.filtered(lambda y: y.year == year_str)
        if year_line and year_line[0].expense_account_id:
            return year_line[0].expense_account_id
        return self.expense_account_id

    def action_view_commission_lines(self):
        """Open commission lines for this scheme."""
        self.ensure_one()
        return {
            'name': _('Commission Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.commission.line',
            'view_mode': 'list,form',
            'domain': [('scheme_id', '=', self.id)],
            'context': {'default_scheme_id': self.id},
        }

