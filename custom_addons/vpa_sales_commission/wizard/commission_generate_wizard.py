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
        inverse='_inverse_total_commission_amount',
        readonly=False,
        digits=(12, 2),
        help='Editable. Type the total commission to pay for this MO — it is '
             'distributed over the selected employees (proportionally when '
             'several) and their rates are back-calculated.',
    )
    manual_commission = fields.Boolean(
        string='Manual Commission',
        help='Tick to enter the commission manually (total, per-employee amount '
             'or rate). Untick to reset everything to the standard year rates.',
    )
    commission_per_item = fields.Float(
        string='Commission Per Item',
        compute='_compute_commission_per_item',
        digits=(12, 2),
        help='Total commission divided by the quantity produced — the '
             'commission carried by each unit of the finished item.',
    )
    total_extra_amount = fields.Float(
        string='Extra vs Standard',
        compute='_compute_total_extra_amount',
        digits=(12, 2),
        help='Total commission above (or below) what the standard year rates '
             'would give for the selected employees.',
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

    @api.depends('total_commission_amount', 'product_qty')
    def _compute_commission_per_item(self):
        for wizard in self:
            if wizard.product_qty:
                wizard.commission_per_item = (
                    wizard.total_commission_amount / wizard.product_qty
                )
            else:
                wizard.commission_per_item = 0.0

    @api.depends('scheme_line_ids.selected', 'scheme_line_ids.extra_amount')
    def _compute_total_extra_amount(self):
        for wizard in self:
            wizard.total_extra_amount = sum(
                l.extra_amount for l in wizard.scheme_line_ids if l.selected)

    @api.onchange('manual_commission')
    def _onchange_manual_commission(self):
        """Unticking resets every line back to its standard year rate."""
        if not self.manual_commission:
            for line in self.scheme_line_ids:
                line.rate = line.standard_rate

    @api.onchange('total_commission_amount')
    def _onchange_total_commission_amount(self):
        """Guarantee live propagation to the employee lines in the dialog."""
        self._inverse_total_commission_amount()

    def _inverse_total_commission_amount(self):
        """Typing the total distributes it over the selected employees
        (proportional to their current amounts) via back-calculated rates."""
        for wizard in self:
            selected = wizard.scheme_line_ids.filtered(
                lambda l: l.selected and not l.already_generated)
            base = wizard.total_base_amount
            if not selected or not base:
                continue
            current = sum(selected.mapped('estimated_amount'))
            for line in selected:
                share = (line.estimated_amount / current) if current else 1.0 / len(selected)
                line.rate = wizard.total_commission_amount * share / base * 100.0

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
                'rate': scheme_line.rate,
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
    commissionable_amount = fields.Float(
        string='Commissionable',
        digits=(12, 2),
        compute='_compute_commissionable_amount',
        store=True,
        help='Total Cost when the line is included, otherwise zero. Summing '
             'this column gives the base amount commission is charged on — '
             'a plain sum of Total Cost would also count excluded lines.',
    )

    @api.depends('included', 'amount')
    def _compute_commissionable_amount(self):
        for line in self:
            line.commissionable_amount = line.amount if line.included else 0.0


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
        help='Editable. Changing the rate recalculates the commission amount.',
    )
    estimated_amount = fields.Float(
        string='Estimated Commission',
        compute='_compute_estimated_amount',
        inverse='_inverse_estimated_amount',
        readonly=False,
        digits=(12, 2),
        help='Editable. Typing an amount back-calculates the rate, so the '
             'generated commission matches exactly what you entered.',
    )
    commission_per_unit = fields.Float(
        string='Per Unit',
        compute='_compute_estimated_amount',
        digits=(12, 2),
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        readonly=True,
    )
    standard_rate = fields.Float(
        string='Standard Rate (%)',
        readonly=True,
        help='The configured rate of the commission year — the baseline.',
    )
    extra_amount = fields.Float(
        string='Extra',
        compute='_compute_extra_amount',
        digits=(12, 2),
        help='How much above (or below) the standard-rate commission this '
             'employee gets with the current amount.',
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

    @api.depends('rate', 'wizard_id.total_base_amount', 'wizard_id.product_qty')
    def _compute_estimated_amount(self):
        for line in self:
            line.estimated_amount = line.wizard_id.total_base_amount * line.rate / 100.0
            if line.wizard_id.product_qty:
                line.commission_per_unit = line.estimated_amount / line.wizard_id.product_qty
            else:
                line.commission_per_unit = 0.0

    @api.depends('estimated_amount', 'standard_rate', 'wizard_id.total_base_amount')
    def _compute_extra_amount(self):
        for line in self:
            standard = line.wizard_id.total_base_amount * line.standard_rate / 100.0
            line.extra_amount = line.estimated_amount - standard

    def _inverse_estimated_amount(self):
        """Typing the amount back-calculates the rate (full precision), so the
        generated commission equals exactly the amount entered."""
        for line in self:
            base = line.wizard_id.total_base_amount
            if base:
                line.rate = line.estimated_amount / base * 100.0


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
