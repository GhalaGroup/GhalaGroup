# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA Unit of Measure',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Product-specific alternative units of measure (v1.0.0)',
    'description': """
VPA Unit of Measure
===================

Product-specific alternative units of measure with custom conversion factors.

Similar to SAP's Alternative Unit of Measure (AUoM) functionality, this module
allows you to define different conversion factors for the same UoM across
different products.

Key Features
------------
* **Product-Specific Conversions**: Define unique conversion factors per product
  (e.g., 1 Board = 2.9768 m² for MDF 18mm, but 1 Board = 2.88 m² for OSB)
* **Sales Integration**: Sell in alternative UoM with automatic conversion
* **Purchase Integration**: Buy in alternative UoM (pallets, boxes, etc.)
* **Stock Transfers**: Transfer inventory using any configured UoM
* **Manufacturing Support**: Use alternative UoM in BOMs and production orders
* **Enhanced Stock Views**: See stock on hand in alternative UoM
* **Product Cards**: View alternative UoM quantities in list and kanban views
* **Configurable Rounding**: Set decimal precision per conversion
* **Backup & Restore**: Export/import conversions, auto-backup before uninstall
* **Multi-Company Support**: Each company can have its own conversion factors
* **Role-Based Security**: User, Manager, and Administrator access levels

Use Cases
---------
* Sheet materials (plywood, MDF) - Store in m², sell in Boards
* Liquids - Store in liters, sell in bottles/containers
* Textiles - Store in meters, sell in rolls
* Hardware - Store in units, sell in boxes/packs

Version History
---------------
* **19.0.1.0.0** - Initial release for Odoo 19
  - Product-specific UoM conversions
  - Sales, Purchase, Stock, MRP integration
  - Enhanced product views with alternative UoM display

Developed by VPA Solutions Limited
Support: info@vpa.co.tz
    """,
    'author': 'VPA Solutions Limited',
    'website': 'https://www.vpa.co.tz',
    'support': 'info@vpa.co.tz',
    'license': 'OPL-1',
    'price': 69.00,
    'currency': 'USD',
    'depends': [
        'product',
        'stock',
        'sale_stock',
        'purchase_stock',
        'mrp',
        'uom',
    ],
    'data': [
        'security/vpa_uom_security.xml',
        'security/ir.model.access.csv',
        'views/product_uom_conversion_views.xml',
        'views/product_views.xml',
        'views/mrp_production_views.xml',
        'views/menus.xml',
        'views/backup_views.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
