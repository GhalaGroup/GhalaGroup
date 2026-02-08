# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class VpaCommissionLine(models.Model):
    _name = 'vpa.commission.line'
    _description = 'Commission Line'
    _order = 'date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
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

    # Type field for future-proofing (Phase 2: Sales commission)
    type = fields.Selection([
        ('production', 'Production'),
        ('sales', 'Sales'),
    ], string='Type', default='production', required=True)

    date = fields.Date(
        string='Date',
        required=True,
        index=True,
        help='Manufacturing Order completion date',
    )
    @api.model
    def _get_year_selection(self):
        """Generate year selection from 2020 to current year + 2."""
        current_year = fields.Date.today().year
        return [(str(y), str(y)) for y in range(2020, current_year + 3)]

    date_year = fields.Selection(
        selection='_get_year_selection',
        string='Year',
        compute='_compute_date_parts',
        store=True,
        index=True,
    )
    date_month = fields.Char(
        string='Month',
        compute='_compute_date_parts',
        store=True,
        index=True,
    )

    # Source documents
    production_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing Order',
        index=True,
        ondelete='set null',
    )
    sale_order_name = fields.Char(
        string='Sales Order',
        compute='_compute_sale_order_info',
        store=True,
    )
    item_name = fields.Char(
        string='Item',
        compute='_compute_sale_order_info',
        store=True,
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        index=True,
        ondelete='set null',
        help='For future Sales commission (Phase 2)',
    )

    # Commission calculation fields
    base_amount = fields.Float(
        string='Base Amount',
        digits=(12, 2),
        help='Sum of commissionable material costs',
    )
    rate = fields.Float(
        string='Rate (%)',
        digits=(5, 2),
        help='Commission rate applied',
    )
    amount = fields.Float(
        string='Commission Amount',
        digits=(12, 2),
        compute='_compute_amount',
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='scheme_id.currency_id',
        store=True,
    )

    # Status workflow
    state = fields.Selection([
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending', required=True)

    confirmed_date = fields.Date(
        string='Confirmed Date',
        readonly=True,
    )
    confirmed_by = fields.Many2one(
        'res.users',
        string='Confirmed By',
        readonly=True,
    )
    paid_date = fields.Date(
        string='Paid Date',
        readonly=True,
    )
    paid_by = fields.Many2one(
        'res.users',
        string='Paid By',
        readonly=True,
    )
    payment_id = fields.Many2one(
        'account.payment',
        string='Payment',
        readonly=True,
        ondelete='set null',
        index=True,
    )

    amount_paid = fields.Float(
        string='Amount Paid',
        digits=(12, 2),
        compute='_compute_amount_paid',
        store=True,
    )
    amount_due = fields.Float(
        string='Amount Due',
        digits=(12, 2),
        compute='_compute_amount_paid',
        store=True,
    )

    notes = fields.Text(string='Notes')

    # Delivery tracking
    delivered = fields.Boolean(
        string='Delivered',
        compute='_compute_delivered',
        store=True,
        readonly=False,
        help='Auto-detected from Sale Order delivery status. Can be manually overridden.',
    )
    delivery_date = fields.Date(
        string='Delivery Date',
        compute='_compute_delivered',
        store=True,
        readonly=False,
    )

    # Material breakdown
    material_line_ids = fields.One2many(
        'vpa.commission.line.material',
        'commission_line_id',
        string='Materials',
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('vpa.commission.line') or _('New')
        return super().create(vals_list)

    @api.depends('production_id')
    def _compute_delivered(self):
        for line in self:
            if line.production_id and hasattr(line.production_id, 'sale_line_id') and line.production_id.sale_line_id:
                sale_order = line.production_id.sale_line_id.order_id
                done_pickings = sale_order.picking_ids.filtered(
                    lambda p: p.state == 'done' and p.picking_type_code == 'outgoing'
                )
                if done_pickings:
                    line.delivered = True
                    line.delivery_date = done_pickings[0].date_done.date() if done_pickings[0].date_done else False
                else:
                    if not line.delivered:
                        line.delivered = False
                    if not line.delivery_date:
                        line.delivery_date = False
            else:
                if not line.delivered:
                    line.delivered = False
                if not line.delivery_date:
                    line.delivery_date = False

    @api.depends('production_id', 'production_id.sale_line_id.order_id', 'production_id.product_id')
    def _compute_sale_order_info(self):
        for line in self:
            sale_order = False
            if line.production_id and hasattr(line.production_id, 'sale_line_id') and line.production_id.sale_line_id:
                sale_order = line.production_id.sale_line_id.order_id
            line.sale_order_name = sale_order.name if sale_order else (line.production_id.origin or False)
            line.item_name = line.production_id.product_id.name if line.production_id else False

    @api.depends('date')
    def _compute_date_parts(self):
        for line in self:
            if line.date:
                line.date_year = str(line.date.year)
                line.date_month = line.date.strftime('%Y-%m')
            else:
                line.date_year = False
                line.date_month = False

    @api.depends('base_amount', 'rate')
    def _compute_amount(self):
        for line in self:
            line.amount = line.base_amount * line.rate / 100

    @api.depends('amount', 'state')
    def _compute_amount_paid(self):
        for line in self:
            if line.state == 'paid':
                line.amount_paid = line.amount
            else:
                line.amount_paid = 0.0
            line.amount_due = line.amount - line.amount_paid

    def action_confirm(self):
        """Confirm commission lines - only managers can do this."""
        for line in self:
            if line.state != 'pending':
                raise UserError(_('Only pending commission lines can be confirmed.'))
            line.write({
                'state': 'confirmed',
                'confirmed_date': fields.Date.today(),
                'confirmed_by': self.env.uid,
            })

    def action_cancel(self):
        """Cancel commission lines."""
        for line in self:
            if line.state == 'paid':
                raise UserError(_('Paid commission lines cannot be cancelled. Reset to pending first.'))
            line.write({'state': 'cancelled'})

    def action_reset_to_pending(self):
        """Reset confirmed, paid, or cancelled lines back to pending."""
        for line in self:
            if line.state not in ('confirmed', 'paid', 'cancelled'):
                raise UserError(_('Only confirmed, paid, or cancelled commission lines can be reset to pending.'))
            line.write({
                'state': 'pending',
                'confirmed_date': False,
                'confirmed_by': False,
                'paid_date': False,
                'paid_by': False,
                'payment_id': False,
            })

    def action_view_production(self):
        """Open the related manufacturing order."""
        self.ensure_one()
        if not self.production_id:
            raise UserError(_('No manufacturing order linked to this commission line.'))
        return {
            'name': _('Manufacturing Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': self.production_id.id,
        }

    @api.model
    def action_open_commission_payments(self):
        """Open all payments linked to commission lines."""
        payment_ids = self.search([
            ('payment_id', '!=', False),
        ]).mapped('payment_id').ids
        return {
            'name': _('Commission Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', payment_ids)],
            'context': {'create': False},
        }


class VpaCommissionLineMaterial(models.Model):
    _name = 'vpa.commission.line.material'
    _description = 'Commission Line Material'
    _order = 'id'

    commission_line_id = fields.Many2one(
        'vpa.commission.line',
        string='Commission Line',
        required=True,
        ondelete='cascade',
        index=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        readonly=True,
    )
    quantity = fields.Float(
        string='Quantity',
        digits=(12, 4),
        readonly=True,
    )
    unit_cost = fields.Float(
        string='Unit Cost',
        digits=(12, 2),
        readonly=True,
    )
    amount = fields.Float(
        string='Total Cost',
        digits=(12, 2),
        readonly=True,
    )
    included = fields.Boolean(
        string='Included',
        readonly=True,
    )
