# -*- coding: utf-8 -*-
# Part of Product Sequence Configuration. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2025 VPA Software Limited

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # General Settings
    product_sku_auto_generate = fields.Boolean(
        string='Auto-generate SKU on Category Selection',
        config_parameter='vpa_sku_generator.auto_generate',
        default=True,
        help='Automatically generate SKU when a category is selected on product'
    )

    product_sku_block_manual = fields.Boolean(
        string='Block Manual SKU Entry',
        config_parameter='vpa_sku_generator.block_manual',
        default=False,
        help='Prevent users from manually entering or editing SKU (Internal Reference)'
    )

    product_sku_require_category = fields.Boolean(
        string='Require Category',
        config_parameter='vpa_sku_generator.require_category',
        default=True,
        help='Make product category mandatory before saving'
    )

    product_sku_require_sku = fields.Boolean(
        string='Require SKU',
        config_parameter='vpa_sku_generator.require_sku',
        default=True,
        help='Make SKU (Internal Reference) mandatory before saving'
    )

    product_sku_enable_recycle = fields.Boolean(
        string='Enable SKU Recycling',
        config_parameter='vpa_sku_generator.enable_recycle',
        default=True,
        help='Reuse SKUs from deleted products to fill gaps in sequences'
    )

    # Statistics (computed fields for display)
    total_products_with_sku = fields.Integer(
        string='Products with SKU',
        compute='_compute_sku_statistics'
    )

    total_locked_products = fields.Integer(
        string='Locked Products',
        compute='_compute_sku_statistics'
    )

    total_recycled_skus = fields.Integer(
        string='Available Recycled SKUs',
        compute='_compute_sku_statistics'
    )

    total_categories_with_shortcode = fields.Integer(
        string='Categories with Short Code',
        compute='_compute_sku_statistics'
    )

    @api.depends_context('company')
    def _compute_sku_statistics(self):
        for record in self:
            company = record.company_id or self.env.company

            # Count products with SKU in current company
            record.total_products_with_sku = self.env['product.template'].search_count([
                ('default_code', '!=', False),
                ('company_id', 'in', [False, company.id])
            ])

            # Count locked products
            record.total_locked_products = self.env['product.template'].search_count([
                ('sku_locked', '=', True),
                ('company_id', 'in', [False, company.id])
            ])

            # Count recycled SKUs
            record.total_recycled_skus = self.env['product.sku.recycle.pool'].search_count([
                ('company_id', '=', company.id)
            ])

            # Count categories with short codes
            record.total_categories_with_shortcode = self.env['product.category'].search_count([
                ('short_name', '!=', False),
                ('company_id', 'in', [False, company.id])
            ])

    def action_open_regenerate_wizard(self):
        """Open the regenerate SKU wizard"""
        return {
            'name': 'Regenerate Product SKUs',
            'type': 'ir.actions.act_window',
            'res_model': 'regenerate.sku.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    def action_view_categories(self):
        """Open categories SKU management view"""
        list_view_id = self.env.ref('vpa_sku_generator.product_category_list_view_sku').id
        form_view_id = self.env.ref('product.product_category_form_view').id

        return {
            'name': 'Product Categories - SKU Management',
            'type': 'ir.actions.act_window',
            'res_model': 'product.category',
            'view_mode': 'list,form',
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'domain': [],
            'context': {'create': True},
        }

    def action_view_recycle_pool(self):
        """Open recycle pool list view"""
        return {
            'name': 'SKU Recycle Pool',
            'type': 'ir.actions.act_window',
            'res_model': 'product.sku.recycle.pool',
            'view_mode': 'list,form',
            'domain': [('company_id', '=', self.env.company.id)],
        }

    def action_view_locked_products(self):
        """Open locked products list view"""
        return {
            'name': 'Locked Products',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'list,form',
            'domain': [('sku_locked', '=', True)],
        }
