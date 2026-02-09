# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class VpaCommissionGuarantee(models.Model):
    _name = 'vpa.commission.guarantee'
    _description = 'Annual Commission Guarantee'
    _order = 'year desc, employee_id'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
    )
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

    # User-entered fields
    year = fields.Selection(
        selection='_get_year_selection',
        string='Year',
        required=True,
        index=True,
    )

    @api.model
    def _get_year_selection(self):
        """Generate year selection from 2020 to current year + 2."""
        current_year = fields.Date.today().year
        return [(str(y), str(y)) for y in range(2020, current_year + 3)]

    guarantee_amount = fields.Monetary(
        string='Guarantee Amount',
        currency_field='currency_id',
        required=True,
        help='Annual minimum commission guarantee in scheme currency',
    )
    guarantee_amount_usd = fields.Float(
        string='USD Equivalent',
        digits=(12, 2),
        help='USD equivalent for reference only (manually entered)',
    )
    notes = fields.Text(
        string='Notes',
    )

    # Computed totals from commission lines
    total_earned = fields.Monetary(
        string='Total Earned',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
        help='Total commission earned (all non-cancelled lines)',
    )
    total_confirmed = fields.Monetary(
        string='Total Confirmed',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
    )
    total_pending = fields.Monetary(
        string='Total Pending',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
    )

    # Payment totals from commission lines
    total_paid = fields.Monetary(
        string='Total Paid',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
        help='Sum of paid commission line amounts',
    )
    outstanding = fields.Monetary(
        string='Outstanding',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
        help='Total earned minus total paid',
    )
    shortfall = fields.Monetary(
        string='Shortfall',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
        help='How much below the guarantee the earned commission is',
    )
    status = fields.Selection([
        ('on_track', 'On Track'),
        ('shortfall', 'Shortfall'),
        ('no_lines', 'No Lines'),
    ], string='Status', compute='_compute_status')

    # Commission lines for this year (computed domain)
    commission_line_ids = fields.Many2many(
        'vpa.commission.line',
        string='Commission Lines',
        compute='_compute_commission_line_ids',
    )

    # Payment count from paid commission lines
    payment_count = fields.Integer(
        string='Payments',
        compute='_compute_payment_count',
    )

    _guarantee_uniq = models.Constraint(
        'unique(scheme_id, year)',
        'A guarantee already exists for this employee and year!',
    )

    @api.depends('employee_id', 'year')
    def _compute_name(self):
        for guarantee in self:
            if guarantee.employee_id and guarantee.year:
                guarantee.name = f"{guarantee.employee_id.name} - {guarantee.year}"
            else:
                guarantee.name = _('New Guarantee')

    @api.depends(
        'scheme_id.commission_line_ids',
        'scheme_id.commission_line_ids.amount',
        'scheme_id.commission_line_ids.state',
        'scheme_id.commission_line_ids.date_year',
        'guarantee_amount',
        'year',
    )
    def _compute_totals(self):
        for guarantee in self:
            lines = guarantee.scheme_id.commission_line_ids.filtered(
                lambda l: l.date_year == guarantee.year and l.state != 'cancelled'
            )
            guarantee.total_earned = sum(lines.mapped('amount'))
            guarantee.total_confirmed = sum(
                lines.filtered(lambda l: l.state in ('confirmed', 'paid')).mapped('amount')
            )
            guarantee.total_pending = sum(
                lines.filtered(lambda l: l.state == 'pending').mapped('amount')
            )
            guarantee.total_paid = sum(
                lines.filtered(lambda l: l.state == 'paid').mapped('amount')
            )
            guarantee.shortfall = max(0.0, guarantee.guarantee_amount - guarantee.total_earned)
            guarantee.outstanding = max(0.0, guarantee.total_earned - guarantee.total_paid)

    @api.depends('total_earned', 'guarantee_amount', 'scheme_id.commission_line_ids')
    def _compute_status(self):
        for guarantee in self:
            lines = guarantee.scheme_id.commission_line_ids.filtered(
                lambda l: l.date_year == guarantee.year and l.state != 'cancelled'
            )
            if not lines:
                guarantee.status = 'no_lines'
            elif guarantee.total_earned >= guarantee.guarantee_amount:
                guarantee.status = 'on_track'
            else:
                guarantee.status = 'shortfall'

    @api.depends('scheme_id', 'year')
    def _compute_commission_line_ids(self):
        for guarantee in self:
            if guarantee.scheme_id and guarantee.year:
                guarantee.commission_line_ids = guarantee.scheme_id.commission_line_ids.filtered(
                    lambda l: l.date_year == guarantee.year and l.state != 'cancelled'
                )
            else:
                guarantee.commission_line_ids = False

    @api.depends('scheme_id', 'year')
    def _compute_payment_count(self):
        for guarantee in self:
            if guarantee.scheme_id and guarantee.year:
                payment_ids = guarantee.scheme_id.commission_line_ids.filtered(
                    lambda l: l.date_year == guarantee.year and l.state == 'paid' and l.payment_id
                ).mapped('payment_id')
                guarantee.payment_count = len(payment_ids)
            else:
                guarantee.payment_count = 0

    @api.constrains('guarantee_amount')
    def _check_guarantee_amount(self):
        for guarantee in self:
            if guarantee.guarantee_amount < 0:
                raise ValidationError(_('Guarantee amount cannot be negative.'))

    def _get_payment_ids(self):
        """Get unique payment IDs from paid commission lines for this year."""
        self.ensure_one()
        return self.scheme_id.commission_line_ids.filtered(
            lambda l: l.date_year == self.year and l.state == 'paid' and l.payment_id
        ).mapped('payment_id').ids

    def action_view_commission_lines(self):
        """Open commission lines for this guarantee's year."""
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

    def action_print_statement(self):
        """Open the commission statement view for this guarantee."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Commission Statement - %s', self.name),
            'res_model': 'vpa.commission.guarantee',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref(
                'vpa_sales_commission.vpa_commission_guarantee_statement_view_form'
            ).id,
            'target': 'current',
        }

    def action_view_payments(self):
        """Open payments linked to paid commission lines for this year."""
        self.ensure_one()
        payment_ids = self._get_payment_ids()
        return {
            'name': _('Payments - %s (%s)', self.employee_id.name, self.year),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', payment_ids)],
        }
