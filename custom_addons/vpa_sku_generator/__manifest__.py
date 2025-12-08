# -*- coding: utf-8 -*-
# Part of Product Sequence Configuration. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2025 VPA Software Limited
{
    'name': 'VPA SKU Generator',

    'summary': 'Advanced SKU management with auto-generation, category-based sequences, SKU locking, and gap filling',

    'description': """
        Product Sequence Configuration - Professional SKU Management
        ============================================================

        Comprehensive SKU (Internal Reference) management solution with advanced features:

        Key Features:
        -------------
        * Auto-generate SKUs based on category hierarchy (e.g., FUR/TBL/00003)
        * Support for product variants with sequential suffixes (00003-001, 00003-002)
        * Lock individual products to prevent SKU regeneration
        * Recycle deleted product SKUs to eliminate gaps in sequences
        * Block manual SKU entry (optional)
        * Require category assignment before saving products (optional)
        * Comprehensive settings page with 4 tabs:
          - General settings (validation rules, auto-generation options)
          - Category management (short codes, statistics, preview)
          - Sequence overview (company-specific sequences)
          - Recycle pool (available deleted SKUs for reuse)
        * Regenerate SKU wizard with before/after preview
        * Multi-company support

        Perfect for businesses that need:
        ---------------------------------
        * Consistent SKU formatting across all products
        * Category-based product identification
        * Gap-free sequential numbering
        * Protection against accidental SKU changes
        * Professional inventory management

        Compatible with Odoo 19.0
    """,

    'author': 'VPA Software Limited',
    'website': 'https://www.vpasoftware.com',
    'support': 'support@vpasoftware.com',
    'license': 'OPL-1',
    'category': 'Inventory/Inventory',
    'version': '19.0.1.0.4',
    'price': 79.99,
    'currency': 'USD',

    'depends': ['product', 'stock'],

    'pre_init_hook': 'pre_init_hook',

    'data': [
        'security/vpa_sku_generator_security.xml',
        'security/product_category.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/res_config_settings_views.xml',
        'views/product_category_views.xml',
        'views/product_template_views.xml',
        'views/product_sku_recycle_pool_views.xml',
        'wizard/regenerate_sku_wizard_views.xml',
        'data/product_actions.xml',
    ],

    'demo': [],

    'images': ['static/description/banner.png'],

    'installable': True,
    'application': False,
    'auto_install': False,
}
