# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class VpaBomCategory(models.Model):
    """BOM Category for classifying raw materials.

    Similar to SAP BOM Groups, this allows categorizing raw materials
    (Paint, Hardwood, Hinges, etc.) for filtering during material selection
    in Manufacturing Orders.
    """
    _name = 'vpa.bom.category'
    _description = 'BOM Category'
    _order = 'sequence, code'
    _parent_name = 'parent_id'
    _parent_store = True

    code = fields.Char(
        string='Code',
        required=False,
        index=True,
        copy=False,
        help="Optional short code for the category (auto-generated from name if empty)",
    )
    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
        help="Full name of the category (e.g., Paint & Finishes, Hardwood)",
    )
    description = fields.Text(
        string='Description',
        translate=True,
        help="Optional description for this category",
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Used to order categories in dropdowns and lists",
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Uncheck to archive this category",
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        help="Leave empty to share across all companies",
    )
    color = fields.Integer(
        string='Color Index',
        default=0,
        help="Color for Kanban cards",
    )

    # Hierarchy fields
    is_main_category = fields.Boolean(
        string='Main Category',
        default=False,
        help="Check if this is a main category (for grouping only, cannot be assigned to products/BOMs)",
    )
    parent_id = fields.Many2one(
        'vpa.bom.category',
        string='Parent Category',
        ondelete='restrict',
        index=True,
        domain="[('is_main_category', '=', True)]",
        help="Parent category for hierarchical organization (only main categories can be parents)",
    )
    parent_path = fields.Char(
        index=True,
    )
    child_ids = fields.One2many(
        'vpa.bom.category',
        'parent_id',
        string='Subcategories',
        help="Child categories under this category",
    )

    # Related counts
    product_count = fields.Integer(
        string='Products',
        compute='_compute_product_count',
        help="Number of products in this category",
    )
    bom_line_count = fields.Integer(
        string='BOM Lines',
        compute='_compute_bom_line_count',
        help="Number of BOM lines using this category",
    )

    # SQL Constraints
    _sql_constraints = [
        ('name_company_uniq', 'UNIQUE(name, company_id)',
         'Category name must be unique per company!'),
    ]

    @api.depends('name')
    def _compute_display_name(self):
        """Compute display name from name."""
        for category in self:
            category.display_name = category.name or _("New Category")

    def _compute_product_count(self):
        """Count products assigned to this category."""
        for category in self:
            category.product_count = self.env['product.template'].search_count([
                ('bom_category_id', '=', category.id),
            ])

    def _compute_bom_line_count(self):
        """Count BOM lines using this category."""
        for category in self:
            category.bom_line_count = self.env['mrp.bom.line'].search_count([
                ('bom_category_id', '=', category.id),
            ])

    def action_view_products(self):
        """Open list of products in this category."""
        self.ensure_one()
        return {
            'name': _('Products: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'tree,form',
            'domain': [('bom_category_id', '=', self.id)],
            'context': {'default_bom_category_id': self.id, 'default_is_raw_material': True},
        }

    def action_view_bom_lines(self):
        """Open list of BOM lines using this category."""
        self.ensure_one()
        return {
            'name': _('BOM Lines: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom.line',
            'view_mode': 'tree,form',
            'domain': [('bom_category_id', '=', self.id)],
            'context': {'default_bom_category_id': self.id},
        }

    # =========================================================================
    # PLACEHOLDER PRODUCT AUTO-CREATION
    # =========================================================================
    placeholder_product_id = fields.Many2one(
        'product.product',
        string='Placeholder Product',
        readonly=True,
        help="System-generated placeholder product for this category. "
             "Used in MO when creating from Master BOM template lines.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Override to auto-create placeholder product for each new category."""
        records = super().create(vals_list)
        for record in records:
            # Don't create placeholders for main categories (they're for grouping only)
            if not record.is_main_category:
                record._create_placeholder_product()
        return records

    def _create_placeholder_product(self):
        """Create a placeholder product for this category."""
        self.ensure_one()
        if self.placeholder_product_id:
            return  # Already has placeholder

        # Build placeholder name with code if available
        if self.code:
            name = f"[{self.code}] Template - {self.name}"
        else:
            name = f"Template - {self.name}"

        # Create the placeholder product
        product_vals = {
            'name': name,
            'type': 'consu',  # Consumable - no stock tracking
            'is_template_placeholder': True,
            'is_raw_material': True,
            'bom_category_id': self.id,
            'sale_ok': False,
            'purchase_ok': False,
            'list_price': 0.0,
            'standard_price': 0.0,
        }

        product = self.env['product.product'].sudo().create(product_vals)
        self.placeholder_product_id = product.id

    def action_create_placeholder(self):
        """Manually create placeholder product if missing."""
        for record in self:
            if not record.is_main_category and not record.placeholder_product_id:
                record._create_placeholder_product()
        return True
