# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    """Extend product.template with raw material classification."""
    _inherit = 'product.template'

    is_raw_material = fields.Boolean(
        string='Is Raw Material',
        default=False,
        help="Check if this product is a raw material used in manufacturing. "
             "Raw materials can be assigned to BOM Categories for filtering.",
    )
    bom_category_id = fields.Many2one(
        'vpa.bom.category',
        string='BOM Category',
        help="Category for filtering in BOM selection (e.g., Paint, Hardwood, Hinges). "
             "Only applicable when 'Is Raw Material' is checked.",
    )

    @api.onchange('is_raw_material')
    def _onchange_is_raw_material(self):
        """Clear BOM category when not a raw material."""
        if not self.is_raw_material:
            self.bom_category_id = False
