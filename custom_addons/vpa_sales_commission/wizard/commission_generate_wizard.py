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
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        related='production_id.product_uom_id',
        readonly=True,
    )
    cost_per_unit = fields.Float(
        string='Cost Per Unit',
        compute='_compute_cost_per_unit',
        digits=(12, 2),
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
    history_line_ids = fields.One2many(
        'vpa.commission.generate.wizard.history',
        'wizard_id',
        string='Commission History',
    )
    has_history = fields.Boolean(
        string='Has History',
        compute='_compute_has_history',
    )
    total_base_amount = fields.Float(
        string='Total Base Amount',
        compute='_compute_total_base_amount',
        digits=(12, 2),
    )
    total_commission_amount = fields.Float(
        string='Total Commission',
        compute='_compute_total_commission_amount',
        digits=(12, 2),
        help='Sum of all estimated commissions for selected employees',
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
    use_override = fields.Boolean(
        string='Use Historical Base Amount',
        default=False,
    )
    override_base_amount = fields.Float(
        string='Override Base Amount',
        digits=(12, 2),
    )
    override_source = fields.Char(
        string='Override Source',
        readonly=True,
    )

    @api.depends('history_line_ids')
    def _compute_has_history(self):
        for wizard in self:
            wizard.has_history = bool(wizard.history_line_ids)

    @api.depends('material_line_ids.included', 'material_line_ids.amount',
                 'use_override', 'override_base_amount')
    def _compute_total_base_amount(self):
        for wizard in self:
            if wizard.use_override and wizard.override_base_amount > 0:
                wizard.total_base_amount = wizard.override_base_amount
            else:
                wizard.total_base_amount = sum(
                    line.amount for line in wizard.material_line_ids if line.included
                )

    @api.depends('total_base_amount', 'product_qty')
    def _compute_cost_per_unit(self):
        for wizard in self:
            if wizard.product_qty:
                wizard.cost_per_unit = wizard.total_base_amount / wizard.product_qty
            else:
                wizard.cost_per_unit = 0.0

    @api.depends('scheme_line_ids.selected', 'scheme_line_ids.estimated_amount')
    def _compute_total_commission_amount(self):
        for wizard in self:
            wizard.total_commission_amount = sum(
                line.estimated_amount for line in wizard.scheme_line_ids if line.selected
            )

    def action_clear_override(self):
        """Clear the historical base amount override."""
        self.ensure_one()
        self.write({
            'use_override': False,
            'override_base_amount': 0.0,
            'override_source': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.commission.generate.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_generate(self):
        """Generate commission lines based on selected materials and schemes."""
        self.ensure_one()

        # Determine base amount: override or calculated from materials
        if self.use_override and self.override_base_amount > 0:
            base_amount = self.override_base_amount
        else:
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

        # Audit note if override was used
        notes = ''
        if self.use_override and self.override_source:
            notes = _('Base amount from: %s') % self.override_source

        CommissionLine = self.env['vpa.commission.line']
        created_count = 0
        for scheme_line in selected_schemes:
            scheme = scheme_line.scheme_id

            vals = {
                'scheme_id': scheme.id,
                'type': 'production',
                'date': commission_date,
                'production_id': self.production_id.id,
                'base_amount': base_amount,
                'rate': scheme.production_rate,
                'state': 'pending',
                'material_line_ids': material_vals,
            }
            if notes:
                vals['notes'] = notes

            CommissionLine.create(vals)
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


class CommissionGenerateWizardHistory(models.TransientModel):
    _name = 'vpa.commission.generate.wizard.history'
    _description = 'Commission Generate Wizard History'
    _order = 'date desc'

    wizard_id = fields.Many2one(
        'vpa.commission.generate.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    production_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing Order',
        readonly=True,
    )
    production_name = fields.Char(
        string='MO Reference',
        readonly=True,
    )
    date = fields.Date(
        string='Date',
        readonly=True,
    )
    product_qty = fields.Float(
        string='Qty Produced',
        digits=(12, 2),
        readonly=True,
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='UoM',
        readonly=True,
    )
    base_amount = fields.Float(
        string='Base Amount',
        digits=(12, 2),
        readonly=True,
    )
    cost_per_unit = fields.Float(
        string='Per Unit',
        compute='_compute_cost_per_unit',
        digits=(12, 2),
    )
    commission_amount = fields.Float(
        string='Commission Paid',
        digits=(12, 2),
        readonly=True,
        help='Total commission amount that was paid for this MO',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        readonly=True,
    )

    @api.depends('base_amount', 'product_qty')
    def _compute_cost_per_unit(self):
        for line in self:
            if line.product_qty:
                line.cost_per_unit = line.base_amount / line.product_qty
            else:
                line.cost_per_unit = 0.0

    def action_use_this_amount(self):
        """Apply this historical per-unit cost scaled to the current MO quantity."""
        self.ensure_one()
        # Calculate per-unit cost from historical MO and scale to current qty
        if self.product_qty:
            per_unit = self.base_amount / self.product_qty
        else:
            per_unit = self.base_amount
        current_qty = self.wizard_id.product_qty or 1.0
        scaled_amount = per_unit * current_qty
        uom_name = self.product_uom_id.name if self.product_uom_id else ''
        self.wizard_id.write({
            'use_override': True,
            'override_base_amount': scaled_amount,
            'override_source': '%s (%s) - %.2f/%s x %.4f %s' % (
                self.production_name,
                self.date.strftime('%d/%m/%Y') if self.date else '',
                per_unit,
                uom_name,
                current_qty,
                uom_name,
            ),
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.commission.generate.wizard',
            'view_mode': 'form',
            'res_id': self.wizard_id.id,
            'target': 'new',
        }
