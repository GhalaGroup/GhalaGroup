# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CommissionGenerateWizard(models.TransientModel):
    _name = 'vpa.commission.generate.wizard'
    _description = 'Generate Commission Wizard'

    production_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing Order',
        required=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        related='production_id.product_id',
        readonly=True,
    )
    product_qty = fields.Float(
        string='Quantity',
        related='production_id.product_qty',
        readonly=True,
    )
    material_line_ids = fields.One2many(
        'vpa.commission.generate.wizard.line',
        'wizard_id',
        string='Materials',
    )
    scheme_line_ids = fields.One2many(
        'vpa.commission.generate.wizard.scheme',
        'wizard_id',
        string='Commission Schemes',
    )
    total_base_amount = fields.Float(
        string='Total Base Amount',
        compute='_compute_total_base_amount',
        digits=(12, 2),
    )
    commission_date = fields.Date(
        string='Commission Date',
        help='Date to record on commission lines. Defaults to MO start date.',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )

    @api.depends('material_line_ids.included', 'material_line_ids.amount')
    def _compute_total_base_amount(self):
        for wizard in self:
            wizard.total_base_amount = sum(
                line.amount for line in wizard.material_line_ids if line.included
            )

    def action_generate(self):
        """Generate commission lines based on selected materials and schemes."""
        self.ensure_one()

        # Calculate base amount from included materials
        base_amount = sum(
            line.amount for line in self.material_line_ids if line.included
        )
        if base_amount <= 0:
            raise UserError(_('No materials selected for commission calculation.'))

        # Get selected schemes
        selected_schemes = self.scheme_line_ids.filtered(
            lambda s: s.selected and not s.already_generated
        )
        if not selected_schemes:
            raise UserError(_('No employees selected for commission generation.'))

        commission_date = self.commission_date or fields.Date.today()

        # Build material snapshot for commission line
        material_vals = []
        for mat in self.material_line_ids:
            material_vals.append((0, 0, {
                'product_id': mat.product_id.id,
                'quantity': mat.quantity,
                'unit_cost': mat.unit_cost,
                'amount': mat.amount,
                'included': mat.included,
            }))

        CommissionLine = self.env['vpa.commission.line']
        created_count = 0
        for scheme_line in selected_schemes:
            scheme = scheme_line.scheme_id

            CommissionLine.create({
                'scheme_id': scheme.id,
                'type': 'production',
                'date': commission_date,
                'production_id': self.production_id.id,
                'base_amount': base_amount,
                'rate': scheme.production_rate,
                'state': 'pending',
                'material_line_ids': material_vals,
            })
            created_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Commission Generated'),
                'message': _('%d commission line(s) created.') % created_count,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }


class CommissionGenerateWizardLine(models.TransientModel):
    _name = 'vpa.commission.generate.wizard.line'
    _description = 'Commission Generate Wizard Line'

    wizard_id = fields.Many2one(
        'vpa.commission.generate.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
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
        string='Include',
        default=True,
    )


class CommissionGenerateWizardScheme(models.TransientModel):
    _name = 'vpa.commission.generate.wizard.scheme'
    _description = 'Commission Generate Wizard Scheme Line'

    wizard_id = fields.Many2one(
        'vpa.commission.generate.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    scheme_id = fields.Many2one(
        'vpa.commission.scheme',
        string='Commission Scheme',
        readonly=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        readonly=True,
    )
    rate = fields.Float(
        string='Rate (%)',
        digits=(5, 2),
        readonly=True,
    )
    estimated_amount = fields.Float(
        string='Estimated Commission',
        compute='_compute_estimated_amount',
        digits=(12, 2),
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        readonly=True,
    )
    selected = fields.Boolean(
        string='Select',
        default=True,
    )
    already_generated = fields.Boolean(
        string='Already Generated',
        readonly=True,
        help='Commission has already been generated for this employee on this MO',
    )

    @api.depends('rate', 'wizard_id.total_base_amount')
    def _compute_estimated_amount(self):
        for line in self:
            line.estimated_amount = line.wizard_id.total_base_amount * line.rate / 100.0
