# -*- coding: utf-8 -*-
# Part of Product Sequence Configuration. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2025 VPA Software Limited

from odoo import api, fields, models, _


class ProductSkuRecyclePool(models.Model):
    _name = 'product.sku.recycle.pool'
    _description = 'Product SKU Recycle Pool'
    _order = 'category_id, sku_number'

    name = fields.Char(
        string='Full SKU',
        required=True,
        index=True,
        help='Complete SKU including category prefix (e.g., FUR/TBL/00123)'
    )

    sku_number = fields.Integer(
        string='SKU Number',
        required=True,
        help='The numeric part of the SKU sequence'
    )

    category_id = fields.Many2one(
        'product.category',
        string='Category',
        required=True,
        ondelete='cascade',
        index=True
    )

    category_path = fields.Char(
        string='Category Path',
        compute='_compute_category_path',
        store=True,
        help='Full category path (e.g., FUR/TBL)'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    deleted_date = fields.Datetime(
        string='Deleted Date',
        default=fields.Datetime.now,
        help='When the SKU was added to recycle pool'
    )

    original_product_name = fields.Char(
        string='Original Product',
        help='Name of the deleted product for reference'
    )

    _sql_constraints = [
        ('unique_sku_company', 'unique(name, company_id)',
         'This SKU already exists in the recycle pool for this company!')
    ]

    @api.depends('category_id', 'category_id.parent_id')
    def _compute_category_path(self):
        for record in self:
            if record.category_id:
                parent_categories = self.env['product.category'].search([
                    ('id', 'parent_of', record.category_id.id)
                ], order="id asc")
                record.category_path = "/".join(parent_categories.mapped("short_name"))
            else:
                record.category_path = False

    @api.model
    def add_to_pool(self, sku, category, company, product_name=None):
        """Add a SKU to the recycle pool when a product is deleted"""
        # Extract the numeric part from SKU
        if not sku or '/' not in sku:
            return False

        try:
            sku_parts = sku.split('/')
            sku_number = int(sku_parts[-1].split('-')[0])  # Handle variants like 00123-001
        except (ValueError, IndexError):
            return False

        # Check if already in pool
        existing = self.search([
            ('name', '=', sku),
            ('company_id', '=', company.id)
        ])

        if existing:
            return existing

        # Add to pool
        return self.create({
            'name': sku,
            'sku_number': sku_number,
            'category_id': category.id,
            'company_id': company.id,
            'original_product_name': product_name,
        })

    @api.model
    def get_from_pool(self, category, company):
        """Get the lowest available SKU from pool for a category"""
        # Find the lowest SKU number for this category
        recycled = self.search([
            ('category_id', '=', category.id),
            ('company_id', '=', company.id)
        ], order='sku_number asc', limit=1)

        if recycled:
            sku = recycled.name
            recycled.unlink()  # Remove from pool
            return sku

        return False

    def action_remove_from_pool(self):
        """Manual action to remove SKU from recycle pool"""
        self.ensure_one()
        return self.unlink()
