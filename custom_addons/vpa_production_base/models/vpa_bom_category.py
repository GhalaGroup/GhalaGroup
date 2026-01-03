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
        required=True,
        index=True,
        help="Short code for the category (e.g., PAINT, HDWD, HINGE)",
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
    parent_id = fields.Many2one(
        'vpa.bom.category',
        string='Parent Category',
        ondelete='restrict',
        index=True,
        help="Parent category for hierarchical organization",
    )
    parent_path = fields.Char(
        index=True,
        unaccent=False,
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
        ('code_company_uniq', 'UNIQUE(code, company_id)',
         'Category code must be unique per company!'),
    ]

    @api.depends('code', 'name')
    def _compute_display_name(self):
        """Compute display name as 'CODE - Name'."""
        for category in self:
            if category.code and category.name:
                category.display_name = f"[{category.code}] {category.name}"
            else:
                category.display_name = category.name or category.code or _("New Category")

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
