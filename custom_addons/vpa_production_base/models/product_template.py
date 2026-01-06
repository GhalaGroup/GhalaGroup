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
        group_expand='_read_group_bom_category_ids',
        help="Category for filtering in BOM selection (e.g., Paint, Hardwood, Hinges). "
             "Only applicable when 'Is Raw Material' is checked.",
    )
    bom_main_category_id = fields.Many2one(
        'vpa.bom.category',
        string='Main Category',
        related='bom_category_id.parent_id',
        store=True,
        readonly=True,
        help="Parent/Main category of the BOM Category (for information only).",
    )

    @api.model
    def _read_group_bom_category_ids(self, categories, domain):
        """Return all BOM categories for Kanban grouping, even if empty.

        This ensures all BOM category columns are always visible in the
        Raw Materials by Category Kanban view.
        """
        # Return all active non-main categories (subcategories that can be assigned)
        return self.env['vpa.bom.category'].search([
            ('is_main_category', '=', False),
            ('active', '=', True),
        ], order='sequence, code')
    is_template_placeholder = fields.Boolean(
        string='Is Template Placeholder',
        default=False,
        help="System field: True if this product is a placeholder for template BOM lines. "
             "Placeholder products are auto-created for each BOM category and should be "
             "replaced with actual products when creating Manufacturing Orders.",
    )

    @api.onchange('is_raw_material')
    def _onchange_is_raw_material(self):
        """Clear BOM category when not a raw material."""
        if not self.is_raw_material:
            self.bom_category_id = False

    def write(self, vals):
        """Auto-mark as raw material when BOM category is assigned.

        This enables drag-and-drop in the Kanban view to automatically
        mark products as raw materials when assigning a BOM category.
        """
        # If bom_category_id is being set (not cleared), mark as raw material
        if vals.get('bom_category_id') and 'is_raw_material' not in vals:
            vals['is_raw_material'] = True
        return super().write(vals)
