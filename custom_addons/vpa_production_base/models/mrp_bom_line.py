# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MrpBomLine(models.Model):
    """Extend mrp.bom.line with BOM Category support for Master BOM template.

    In a Master BOM, lines can have a Category + Description without a specific product.
    The actual product is selected by the worker during production.
    """
    _inherit = 'mrp.bom.line'
    _order = 'sequence, id'

    # =========================================================================
    # SECTION & NOTE SUPPORT (like Sale Order Lines)
    # =========================================================================
    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False,
        help="Technical field for section and note display"
    )
    sequence = fields.Integer(string='Sequence', default=10)

    # =========================================================================
    # CATEGORY & DESCRIPTION FIELDS
    # =========================================================================
    bom_category_id = fields.Many2one(
        'vpa.bom.category',
        string='BOM Category',
        help="Category for filtering products during material selection. "
             "When set without a product, this creates a 'template' line.",
    )
    line_description = fields.Char(
        string='Description',
        help="Description like 'Sealer', 'Top Coat', 'Frame Wood'. "
             "Displayed on MO for worker reference.",
    )

    # Override product_id to make it not required for sections
    product_id = fields.Many2one(
        'product.product',
        domain="[('product_tmpl_id.is_raw_material', '=', True), '|', ('product_tmpl_id.bom_category_id', '=', False), ('product_tmpl_id.bom_category_id', '=', bom_category_id)]",
        required=False,  # Allow empty for sections/notes
    )

    # =========================================================================
    # TEMPLATE LINE DETECTION
    # =========================================================================
    is_template_line = fields.Boolean(
        string='Is Template Line',
        compute='_compute_is_template_line',
        store=True,
        help="True if this is a template line (category set, no specific product). "
             "Worker must select the actual product during production.",
    )

    # =========================================================================
    # MAIN CATEGORY DISPLAY
    # =========================================================================
    main_category_name = fields.Char(
        string='Main Category',
        compute='_compute_main_category_name',
        store=True,
        help="Main category name for grouping (e.g., PAINT, ACCESSORIES)",
    )

    @api.depends('bom_category_id', 'bom_category_id.parent_id')
    def _compute_main_category_name(self):
        """Get the main category name from the selected category."""
        for line in self:
            if line.bom_category_id:
                # If category has a parent (it's a subcategory), use parent name
                if line.bom_category_id.parent_id:
                    line.main_category_name = line.bom_category_id.parent_id.name.upper()
                else:
                    # If no parent, use the category itself
                    line.main_category_name = line.bom_category_id.name.upper()
            else:
                line.main_category_name = False

    @api.depends('bom_category_id', 'product_id')
    def _compute_is_template_line(self):
        """A template line has a category but no specific product."""
        for line in self:
            line.is_template_line = bool(line.bom_category_id and not line.product_id)

    # =========================================================================
    # DISPLAY NAME
    # =========================================================================
    @api.depends('product_id', 'bom_category_id', 'line_description')
    def _compute_display_name(self):
        """Show category and description for template lines."""
        for line in self:
            if line.is_template_line:
                parts = []
                if line.bom_category_id:
                    parts.append(f"[{line.bom_category_id.code}]")
                if line.line_description:
                    parts.append(line.line_description)
                line.display_name = ' '.join(parts) if parts else _("Template Line")
            elif line.product_id:
                line.display_name = line.product_id.display_name
            else:
                line.display_name = _("New Line")

    # =========================================================================
    # VALIDATION
    # =========================================================================
    @api.constrains('bom_category_id', 'product_id')
    def _check_category_product_consistency(self):
        """Validate that lines have either product or category (or both)."""
        for line in self:
            # A line must have at least one of: product_id or bom_category_id
            if not line.product_id and not line.bom_category_id:
                # Standard Odoo BOM line requires product_id, but we allow template lines
                # So this is just a note - the original constraint from mrp handles this
                pass

    @api.onchange('bom_category_id')
    def _onchange_bom_category_id(self):
        """When category is set, filter product dropdown to that category."""
        if self.bom_category_id:
            # If product is set and doesn't match category, clear it
            if self.product_id and self.product_id.product_tmpl_id.bom_category_id != self.bom_category_id:
                self.product_id = False
            # Return domain to filter products
            return {
                'domain': {
                    'product_id': [
                        ('product_tmpl_id.is_raw_material', '=', True),
                        ('product_tmpl_id.bom_category_id', '=', self.bom_category_id.id),
                    ]
                }
            }
        return {'domain': {'product_id': [('product_tmpl_id.is_raw_material', '=', True)]}}

    @api.onchange('product_id')
    def _onchange_product_id_category(self):
        """Auto-fill category from product if product has one."""
        if self.product_id and self.product_id.product_tmpl_id.bom_category_id:
            self.bom_category_id = self.product_id.product_tmpl_id.bom_category_id
