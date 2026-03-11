# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AdjustMaterialsWizard(models.TransientModel):
    _name = 'vpa.adjust.materials.wizard'
    _description = 'Adjust Commission Materials'

    commission_line_id = fields.Many2one(
        'vpa.commission.line',
        string='Commission Line',
        required=True,
        readonly=True,
    )
    line_ids = fields.One2many(
        'vpa.adjust.materials.wizard.line',
        'wizard_id',
        string='Materials',
    )

    # Display fields
    employee_name = fields.Char(
        related='commission_line_id.employee_id.name',
        string='Employee',
    )
    production_name = fields.Char(
        related='commission_line_id.production_id.name',
        string='Manufacturing Order',
    )
    current_base_amount = fields.Float(
        related='commission_line_id.base_amount',
        string='Current Base Amount',
    )
    new_base_amount = fields.Float(
        string='New Base Amount',
        compute='_compute_new_base_amount',
    )
    rate = fields.Float(
        related='commission_line_id.rate',
        string='Rate (%)',
    )
    new_commission_amount = fields.Float(
        string='New Commission Amount',
        compute='_compute_new_base_amount',
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='commission_line_id.currency_id',
    )

    @api.depends('line_ids.included', 'line_ids.amount')
    def _compute_new_base_amount(self):
        for wizard in self:
            wizard.new_base_amount = sum(
                line.amount for line in wizard.line_ids if line.included
            )
            wizard.new_commission_amount = wizard.new_base_amount * wizard.rate / 100 if wizard.rate else 0.0

    def action_apply(self):
        """Apply material adjustments to the commission line."""
        self.ensure_one()
        commission_line = self.commission_line_id

        if commission_line.state in ('paid', 'cancelled'):
            raise UserError(_('Cannot adjust materials on a paid or cancelled commission line.'))

        # Track changes for chatter
        added = []
        removed = []
        for wiz_line in self.line_ids:
            material = wiz_line.material_line_id
            if wiz_line.included and not material.included:
                added.append(material.product_id.name)
            elif not wiz_line.included and material.included:
                removed.append(material.product_id.name)

        # Apply changes
        for wiz_line in self.line_ids:
            wiz_line.material_line_id.included = wiz_line.included

        # Log changes in notes
        if added or removed:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            user_name = self.env.user.name
            log_parts = ['\n--- Materials Adjusted by %s on %s ---' % (user_name, timestamp)]
            for name in added:
                log_parts.append('  + Added: %s' % name)
            for name in removed:
                log_parts.append('  - Removed: %s' % name)
            log_parts.append('  Base Amount: %.2f → %.2f' % (self.current_base_amount, self.new_base_amount))
            existing_notes = commission_line.notes or ''
            commission_line.notes = existing_notes + '\n'.join(log_parts)

        return {'type': 'ir.actions.act_window_close'}


class AdjustMaterialsWizardLine(models.TransientModel):
    _name = 'vpa.adjust.materials.wizard.line'
    _description = 'Adjust Commission Materials Wizard Line'

    wizard_id = fields.Many2one(
        'vpa.adjust.materials.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    material_line_id = fields.Many2one(
        'vpa.commission.line.material',
        string='Material Line',
        required=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        related='material_line_id.product_id',
    )
    quantity = fields.Float(
        string='Quantity',
        related='material_line_id.quantity',
    )
    unit_cost = fields.Float(
        string='Unit Cost',
        related='material_line_id.unit_cost',
    )
    amount = fields.Float(
        string='Total Cost',
        related='material_line_id.amount',
    )
    included = fields.Boolean(
        string='Included',
    )
