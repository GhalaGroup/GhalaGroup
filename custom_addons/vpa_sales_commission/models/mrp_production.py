# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

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

    @api.depends('move_raw_ids', 'move_raw_ids.state', 'move_raw_ids.product_id', 'move_raw_ids.quantity')
    def _compute_commission_base_amount(self):
        for production in self:
            base_amount = 0.0
            for move in production.move_raw_ids.filtered(lambda m: m.state == 'done'):
                if not move.product_id.not_commissionable:
                    base_amount += move.product_id.standard_price * move.quantity
            production.commission_base_amount = base_amount

    def action_generate_commission(self):
        """Create and open the commission generation wizard."""
        self.ensure_one()

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

        # Create wizard record with all data persisted
        wizard = self.env['vpa.commission.generate.wizard'].create({
            'production_id': self.id,
            'commission_date': (
                self.date_start.date() if self.date_start else fields.Date.today()
            ),
            'material_line_ids': material_lines,
            'scheme_line_ids': scheme_lines,
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
