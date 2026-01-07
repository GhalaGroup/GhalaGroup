# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductAssignBomCategory(models.TransientModel):
    """Wizard to quickly assign BOM category to products."""
    _name = 'product.assign.bom.category'
    _description = 'Assign BOM Category to Product'

    product_template_ids = fields.Many2many(
        'product.template',
        string='Products',
        required=True,
    )
    bom_category_id = fields.Many2one(
        'vpa.bom.category',
        string='BOM Category',
        required=True,
        domain=[('is_main_category', '=', False)],
        help="Select the BOM category to assign to the selected products.",
    )

    @api.model
    def default_get(self, fields_list):
        """Set default products and current category from context."""
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        if active_ids and 'product_template_ids' in fields_list:
            res['product_template_ids'] = [(6, 0, active_ids)]
            # Pre-select current category if single product
            if len(active_ids) == 1:
                product = self.env['product.template'].browse(active_ids[0])
                if product.bom_category_id:
                    res['bom_category_id'] = product.bom_category_id.id
        return res

    def action_assign(self):
        """Assign the selected BOM category to products."""
        self.ensure_one()
        # bom_category_id triggers auto-set of is_raw_material in write()
        self.product_template_ids.write({
            'bom_category_id': self.bom_category_id.id,
        })
        return {'type': 'ir.actions.act_window_close'}
