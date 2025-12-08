# -*- coding: utf-8 -*-
# Part of Product Sequence Configuration. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2025 VPA Software Limited

from odoo import models, fields, api, _


class ProductCategory(models.Model):
    _inherit = "product.category"

    short_name = fields.Char(
        string="Category Short Name",
        required=False,
        help="Short code used in SKU generation (e.g., FUR, TBL)"
    )

    company_id = fields.Many2one(
        'res.company',
        required=False,
        default=lambda self: self.env.company
    )

    # Statistics
    product_count = fields.Integer(
        string='Products',
        compute='_compute_product_statistics'
    )

    product_with_sku_count = fields.Integer(
        string='Products with SKU',
        compute='_compute_product_statistics'
    )

    locked_product_count = fields.Integer(
        string='Locked Products',
        compute='_compute_product_statistics'
    )

    sku_preview = fields.Char(
        string='SKU Preview',
        compute='_compute_sku_preview',
        help='Preview of how SKU will look for products in this category'
    )

    sequence_id = fields.Many2one(
        'ir.sequence',
        string='Sequence',
        compute='_compute_sequence_id',
        help='The sequence used for this category'
    )

    next_sku_number = fields.Integer(
        string='Next SKU Number',
        compute='_compute_sequence_id'
    )

    @api.depends('name')
    def _compute_product_statistics(self):
        """Compute product statistics for this category

        Uses product.product (variants) for accurate SKU counting since
        SKUs are typically assigned at the variant level.
        """
        for category in self:
            # Use product.product for accurate variant-level statistics
            products = self.env['product.product'].search([('categ_id', '=', category.id)])
            category.product_count = len(products)
            category.product_with_sku_count = len(products.filtered(lambda p: p.default_code and p.default_code != 'False'))
            category.locked_product_count = len(products.filtered('sku_locked'))

    @api.depends('short_name', 'parent_id', 'parent_id.short_name')
    def _compute_sku_preview(self):
        for category in self:
            if category.short_name:
                parent_categories = self.env['product.category'].search([
                    ('id', 'parent_of', category.id)
                ], order="id asc")

                if all(cat.short_name for cat in parent_categories):
                    short_names = "/".join(parent_categories.mapped("short_name"))
                    category.sku_preview = f"{short_names}/00001"
                else:
                    category.sku_preview = "Missing parent short codes"
            else:
                category.sku_preview = "No short code set"

    def _get_max_sku_number_from_products(self):
        """Scan products to find highest SKU sequence number for imported products.

        This handles cases where products were imported with SKUs directly,
        bypassing the sequence creation. Returns the highest number found
        so the next SKU can continue from there.
        """
        self.ensure_one()
        if not self.short_name:
            return 0

        # Build SKU prefix from category hierarchy
        parent_categories = self.env['product.category'].search([
            ('id', 'parent_of', self.id)
        ], order="id asc")

        if not all(cat.short_name for cat in parent_categories):
            return 0

        sku_prefix = "/".join(parent_categories.mapped("short_name")) + "/"

        # Search products with matching SKUs
        products = self.env['product.product'].search([
            ('categ_id', '=', self.id),
            ('default_code', '!=', False),
            ('default_code', '=like', sku_prefix + '%')
        ])

        max_number = 0
        for product in products:
            sku = product.default_code
            if not sku or not sku.startswith(sku_prefix):
                continue
            try:
                remainder = sku[len(sku_prefix):]
                # Handle variant suffix (e.g., 00001-001 -> 00001)
                number_part = remainder.split('-')[0]
                sku_number = int(number_part)
                max_number = max(max_number, sku_number)
            except (ValueError, IndexError):
                continue

        return max_number

    def _get_sequence_code(self):
        """Build sequence code from full category hierarchy path"""
        self.ensure_one()
        if not self.short_name:
            return False

        # Build path from all parent categories
        parent_categories = self.env['product.category'].search([
            ('id', 'parent_of', self.id)
        ], order="id asc")

        if not all(cat.short_name for cat in parent_categories):
            return False

        # Use full path for unique sequence code (e.g., "UDI_OFF" for UDI/OFF category)
        path = "_".join(parent_categories.mapped("short_name"))
        company_id = self.company_id.id or self.env.company.id
        return f"product_category_{path}_{company_id}"

    @api.depends('short_name', 'company_id', 'parent_id', 'parent_id.short_name')
    def _compute_sequence_id(self):
        for category in self:
            sequence_code = category._get_sequence_code()
            if sequence_code:
                sequence = self.env['ir.sequence'].sudo().search([
                    ('code', '=', sequence_code),
                    ('company_id', '=', category.company_id.id or self.env.company.id)
                ], limit=1)

                category.sequence_id = sequence

                if sequence:
                    category.next_sku_number = sequence.number_next_actual
                else:
                    # No sequence - detect from existing products (handles imports)
                    max_sku = category._get_max_sku_number_from_products()
                    category.next_sku_number = max_sku + 1 if max_sku > 0 else 1
            else:
                category.sequence_id = False
                category.next_sku_number = 0

    def action_view_products(self):
        """Open products with variants in this category"""
        self.ensure_one()
        return {
            'name': _('Products in %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'list,form',
            'domain': [('categ_id', '=', self.id)],
            'context': {
                'default_categ_id': self.id,
                'search_default_categ_id': self.id,
            },
        }

    def action_reset_sequence(self):
        """Reset sequence for this category"""
        self.ensure_one()
        if self.sequence_id:
            return {
                'name': _('Reset Sequence'),
                'type': 'ir.actions.act_window',
                'res_model': 'ir.sequence',
                'res_id': self.sequence_id.id,
                'view_mode': 'form',
                'target': 'new',
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Sequence'),
                    'message': _('No sequence exists for this category yet.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

