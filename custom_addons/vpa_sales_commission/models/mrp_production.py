# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    commission_blocked = fields.Boolean(
        string='Commission Blocked',
        default=False,
        tracking=True,
        groups='vpa_sales_commission.group_commission_user',
        help='If checked, commission cannot be generated for this Manufacturing Order.',
    )

    commission_line_ids = fields.One2many(
        'vpa.commission.line',
        'production_id',
        string='Commission Lines',
        groups='vpa_sales_commission.group_commission_manager',
    )
    commission_line_count = fields.Integer(
        string='Commission Count',
        compute='_compute_commission_line_count',
    )
    commission_generated = fields.Boolean(
        string='Commission Generated',
        compute='_compute_commission_generated',
        store=True,
        help='Commission has been generated for this MO',
    )
    commission_status = fields.Selection([
        ('none', 'No Commission'),
        ('blocked', 'Blocked'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('cancelled', 'Cancelled'),
    ], string='Commission Status',
        compute='_compute_commission_status',
        store=True,
    )

    commission_base_amount = fields.Float(
        string='Commission Base Amount',
        compute='_compute_commission_base_amount',
        digits=(12, 2),
        groups='vpa_sales_commission.group_commission_manager',
        help='Total value of commissionable raw materials consumed',
    )

    @api.depends('commission_line_ids')
    def _compute_commission_line_count(self):
        for production in self:
            production.commission_line_count = len(production.commission_line_ids)

    @api.depends('commission_line_ids')
    def _compute_commission_generated(self):
        for production in self:
            production.commission_generated = bool(production.commission_line_ids)

    @api.depends('commission_line_ids', 'commission_line_ids.state', 'commission_blocked')
    def _compute_commission_status(self):
        for production in self:
            if production.commission_blocked:
                production.commission_status = 'blocked'
            elif not production.commission_line_ids:
                production.commission_status = 'none'
            else:
                states = set(production.commission_line_ids.mapped('state'))
                # Remove cancelled from consideration
                active_states = states - {'cancelled'}
                if not active_states:
                    # All lines are cancelled
                    production.commission_status = 'cancelled'
                elif active_states == {'paid'}:
                    production.commission_status = 'paid'
                elif active_states == {'confirmed'}:
                    production.commission_status = 'confirmed'
                elif active_states == {'pending'}:
                    production.commission_status = 'pending'
                else:
                    # Mix of states
                    production.commission_status = 'partial'

    @api.depends('move_raw_ids', 'move_raw_ids.state', 'move_raw_ids.product_id', 'move_raw_ids.quantity')
    def _compute_commission_base_amount(self):
        for production in self:
            base_amount = 0.0
            for move in production.move_raw_ids.filtered(lambda m: m.state == 'done'):
                if not move.product_id.not_commissionable:
                    base_amount += move.product_id.standard_price * move.quantity
            production.commission_base_amount = base_amount

    def action_block_commission(self):
        """Block commission generation for this MO."""
        self.ensure_one()
        self.commission_blocked = True

    def action_unblock_commission(self):
        """Unblock commission generation for this MO. Manager only."""
        self.ensure_one()
        self.commission_blocked = False

    def action_generate_commission(self):
        """Create and open the commission generation wizard."""
        self.ensure_one()
        if self.commission_blocked:
            raise UserError(_('Commission generation is blocked for this Manufacturing Order.'))

        # Build material lines
        material_lines = []
        for move in self.move_raw_ids.filtered(lambda m: m.state == 'done'):
            material_lines.append((0, 0, {
                'product_id': move.product_id.id,
                'quantity': move.quantity,
                'unit_cost': move.product_id.standard_price,
                'amount': move.product_id.standard_price * move.quantity,
                'included': not move.product_id.not_commissionable,
            }))

        # Build scheme lines
        CommissionLine = self.env['vpa.commission.line']
        schemes = self.env['vpa.commission.scheme'].search([
            ('active', '=', True),
            ('production_commission', '=', True),
            ('production_rate', '>', 0),
            ('company_id', '=', self.company_id.id),
        ])
        scheme_lines = []
        for scheme in schemes:
            if not scheme._applies_to_production(self):
                continue
            existing = CommissionLine.search([
                ('production_id', '=', self.id),
                ('scheme_id', '=', scheme.id),
            ], limit=1)
            scheme_lines.append((0, 0, {
                'scheme_id': scheme.id,
                'employee_id': scheme.employee_id.id,
                'rate': scheme.production_rate,
                'currency_id': scheme.currency_id.id,
                'selected': not bool(existing),
                'already_generated': bool(existing),
            }))

        # Build commission history for this product variant
        history_lines = []
        past_commissions = self.env['vpa.commission.line'].search([
            ('type', '=', 'production'),
            ('production_id', '!=', self.id),
            ('production_id.product_id', '=', self.product_id.id),
            ('state', '!=', 'cancelled'),
        ], order='date desc')
        seen_productions = {}
        for cl in past_commissions:
            if cl.production_id.id not in seen_productions:
                seen_productions[cl.production_id.id] = {
                    'production_id': cl.production_id.id,
                    'production_name': cl.production_id.name,
                    'date': cl.date,
                    'product_qty': cl.production_id.product_qty,
                    'base_amount': cl.base_amount,
                    'commission_amount': cl.amount,
                    'currency_id': cl.currency_id.id,
                }
            else:
                # Aggregate commission amounts for this MO
                seen_productions[cl.production_id.id]['commission_amount'] += cl.amount

        for prod_data in seen_productions.values():
            history_lines.append((0, 0, prod_data))

        # Create wizard record with all data persisted
        wizard = self.env['vpa.commission.generate.wizard'].create({
            'production_id': self.id,
            'commission_date': (
                self.date_finished.date() if self.date_finished else fields.Date.today()
            ),
            'material_line_ids': material_lines,
            'scheme_line_ids': scheme_lines,
            'history_line_ids': history_lines,
        })

        return {
            'name': _('Generate Commission'),
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.commission.generate.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }

    def action_view_commission_lines(self):
        """Open commission lines for this MO."""
        self.ensure_one()
        return {
            'name': _('Commission Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.commission.line',
            'view_mode': 'list,form',
            'domain': [('production_id', '=', self.id)],
            'context': {'default_production_id': self.id},
        }
