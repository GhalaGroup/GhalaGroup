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
        """Compute product statistics for this category"""
        for category in self:
            products = self.env['product.template'].search([('categ_id', '=', category.id)])
            category.product_count = len(products)
            category.product_with_sku_count = len(products.filtered('default_code'))
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

    @api.depends('short_name', 'company_id')
    def _compute_sequence_id(self):
        for category in self:
            if category.short_name:
                sequence_code = f"product_category_{category.short_name}_{category.company_id.id or self.env.company.id}"
                sequence = self.env['ir.sequence'].sudo().search([
                    ('code', '=', sequence_code),
                    ('company_id', '=', category.company_id.id or self.env.company.id)
                ], limit=1)

                category.sequence_id = sequence
                category.next_sku_number = sequence.number_next_actual if sequence else 1
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

