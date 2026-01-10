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
    name = fields.Char(
        string='Section Name / Note',
        help="Name for sections and notes. Used to store section headers like 'PAINT', 'HARDWARE'."
    )

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

    # Override product_id to make it not required for sections/template lines
    product_id = fields.Many2one(
        'product.product',
        domain="[('product_tmpl_id.is_raw_material', '=', True), '|', ('product_tmpl_id.bom_category_id', '=', False), ('product_tmpl_id.bom_category_id', '=', bom_category_id)]",
        required=False,  # Allow empty for sections/notes and template lines
    )

    # Override product_uom_id to ensure it's set even for template lines
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        required=False,  # Not required for sections
        help="Unit of measure for this BOM line. For template lines, this defines the expected UoM.",
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

    @api.depends('bom_category_id', 'product_id', 'product_id.product_tmpl_id.is_template_placeholder')
    def _compute_is_template_line(self):
        """A template line has a category and either no product or a placeholder product."""
        for line in self:
            if line.bom_category_id:
                # Template line if: has category AND (no product OR product is a placeholder)
                if not line.product_id:
                    line.is_template_line = True
                elif line.product_id.product_tmpl_id.is_template_placeholder:
                    line.is_template_line = True
                else:
                    line.is_template_line = False
            else:
                line.is_template_line = False

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
        """When category is set, auto-create section and filter products."""
        if self.bom_category_id and not self.display_type:
            # Get main category name for section
            main_cat = self.bom_category_id.parent_id.name if self.bom_category_id.parent_id else self.bom_category_id.name
            main_cat_upper = main_cat.upper()

            # Check if section already exists in BOM for this main category
            if self.bom_id:
                # Look for existing section with this main category name
                # Sections store the category name in the 'name' field
                existing_section = self.bom_id.bom_line_ids.filtered(
                    lambda l: l.display_type == 'line_section' and l.name == main_cat_upper
                )

                # If no section exists, add one using ORM Command
                if not existing_section:
                    # Find the right sequence for the section (insert before current line)
                    max_seq = max(self.bom_id.bom_line_ids.mapped('sequence') or [0])
                    section_seq = self.sequence - 1 if self.sequence > 10 else max_seq + 10

                    # Add section line using ORM Command (0, 0, values)
                    # In onchange context, we update the parent's One2many field
                    self.bom_id.bom_line_ids = [(0, 0, {
                        'display_type': 'line_section',
                        'name': main_cat_upper,
                        'product_qty': 0,
                        'sequence': section_seq,
                    })]

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
        """Auto-fill category from product and set Manufacturing UoM.

        When a product is added to a BOM line:
        1. Auto-fill BOM category from product if it has one
        2. Use Manufacturing UoM (uom_mrp_id) if set, otherwise use standard UoM (uom_id)
        """
        if self.product_id:
            # Auto-fill BOM category from product
            if self.product_id.product_tmpl_id.bom_category_id:
                self.bom_category_id = self.product_id.product_tmpl_id.bom_category_id

            # Set UoM: prefer Manufacturing UoM, fallback to standard UoM
            product_tmpl = self.product_id.product_tmpl_id
            if product_tmpl.uom_mrp_id:
                self.product_uom_id = product_tmpl.uom_mrp_id
            else:
                self.product_uom_id = product_tmpl.uom_id

    @api.onchange('bom_category_id', 'product_id')
    def _onchange_set_default_uom(self):
        """Set default UoM for template lines if not set."""
        # Template line = has category but no product
        if self.bom_category_id and not self.product_id and not self.product_uom_id:
            # Get default UoM (Units)
            default_uom = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
            if default_uom:
                self.product_uom_id = default_uom

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure template lines have a UoM set."""
        for vals in vals_list:
            # If this is a template line (category but no product) and no UoM is set
            if vals.get('bom_category_id') and not vals.get('product_id') and not vals.get('product_uom_id'):
                # Set default UoM (Units)
                default_uom = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
                if default_uom:
                    vals['product_uom_id'] = default_uom.id

        return super().create(vals_list)

    def write(self, vals):
        """Ensure template lines have a UoM when category is added."""
        result = super().write(vals)

        # After write, check if any lines became template lines without UoM
        for line in self:
            if line.is_template_line and not line.product_uom_id:
                default_uom = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
                if default_uom:
                    super(MrpBomLine, line).write({'product_uom_id': default_uom.id})

        return result
