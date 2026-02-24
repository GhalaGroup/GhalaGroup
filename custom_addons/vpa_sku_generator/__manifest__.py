# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA SKU Generator',
    'version': '19.0.1.0.7',
    'category': 'Inventory/Inventory',
    'summary': 'Advanced SKU management with auto-generation, category-based sequences, SKU locking, and gap filling (v1.0.7)',
    'description': """
VPA SKU Generator
=================

Professional SKU (Internal Reference) management for Odoo 19 Enterprise.

Key Features
------------
* **Auto-Generation**: Generate SKUs based on category hierarchy (e.g., FUR/TBL/00003)
* **Variant Support**: Sequential suffixes for product variants (00003-001, 00003-002)
* **SKU Locking**: Lock individual products to prevent SKU regeneration
* **Gap Filling**: Recycle deleted product SKUs to eliminate gaps in sequences
* **Manual Entry Control**: Block manual SKU entry (optional)
* **Category Requirement**: Require category assignment before saving products (optional)
* **Comprehensive Settings**: 4-tab settings page
  - General settings (validation rules, auto-generation options)
  - Category management (short codes, statistics, preview)
  - Sequence overview (company-specific sequences)
  - Recycle pool (available deleted SKUs for reuse)
* **Regenerate Wizard**: SKU regeneration with before/after preview
* **Multi-Company**: Full multi-company support

Perfect For
-----------
* Consistent SKU formatting across all products
* Category-based product identification
* Gap-free sequential numbering
* Protection against accidental SKU changes
* Professional inventory management

Version History
---------------
* **19.0.1.0.7** - Internal Reference field always readonly (auto-generated SKUs cannot be manually edited)
* **19.0.1.0.6** - Stability and maintenance release
* **19.0.1.0.2** - Bug fixes for category hierarchy and recycle pool
* **19.0.1.0.1** - Settings page UI/UX improvements
* **19.0.1.0.0** - Initial release for Odoo 19

Developed by VPA Solutions Limited
Support: info@vpa.co.tz
    """,
    'author': 'VPA Solutions Limited',
    'website': 'https://www.vpa.co.tz',
    'license': 'OPL-1',
    'price': 79.99,
    'currency': 'USD',
    'depends': [
        'product',
        'stock',
        'vpa_uom',
    ],
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
    'images': [
        'static/description/icon.png',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'pre_init_hook': 'pre_init_hook',
}
