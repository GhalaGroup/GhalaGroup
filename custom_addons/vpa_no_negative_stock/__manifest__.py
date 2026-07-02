# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA Stock Sentinel',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Prevent negative stock with hard-block or soft-warn per company, '
               'manager override, block log and cleanup report (v1.0.0)',
    'description': """
VPA Stock Sentinel
==================

Stop negative stock in Odoo 19 Enterprise - under your control.

By default Odoo allows on-hand stock to go negative across deliveries, transfers,
manufacturing consumption, scrap, inventory adjustments and Point of Sale. VPA
Stock Sentinel enforces non-negative inventory at the single point every stock
decrement passes through, so no pathway slips past it.

Key Features
------------
* **Per-Company Control**: Enable enforcement and choose the mode for each company
  from Inventory > Settings - no effect until you switch it on.
* **Two Modes**:
  - **Hard Block**: The operation is stopped with a clear, detailed error.
  - **Soft Warn (Manager Override)**: Only an Inventory Manager can push the
    operation through, and only after entering a mandatory reason that is logged.
* **Full Coverage**: Deliveries, internal transfers, manufacturing component
  consumption, scrap orders, inventory adjustments and POS pickings.
* **3-Tier Exceptions**: Allow negatives for a specific product, a product
  category (inherited by child categories) or a stock location.
* **Block Log**: Every block, warning and override is recorded with the product,
  location, warehouse, on-hand quantity, requested quantity, shortfall, user,
  document reference and reason - with full chatter.
* **Manager Alerts**: Notify chosen users with a to-do activity when a block or
  override happens.
* **Rich Error Messages**: Shows product, location, on-hand, requested quantity,
  resulting quantity and the exact shortfall.
* **Cleanup Report**: List of products that are currently negative so you can fix
  existing data before turning enforcement on.
* **Multi-Company**: Full multi-company support.

Version History
---------------
* **19.0.1.0.0** - Initial release for Odoo 19

Developed by VPA Solutions Limited
Support: info@vpa.co.tz
    """,
    'author': 'VPA Solutions Limited',
    'website': 'https://www.vpa.co.tz',
    'support': 'info@vpa.co.tz',
    'license': 'OPL-1',
    'price': 99.00,
    'currency': 'USD',
    'depends': [
        'stock',
        'mail',
    ],
    'data': [
        'security/stock_sentinel_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'wizard/negative_override_wizard_views.xml',
        'wizard/adjustment_wizards_views.xml',
        'views/res_config_settings_views.xml',
        'views/stock_sentinel_log_views.xml',
        'views/stock_adjustment_request_views.xml',
        'views/product_views.xml',
        'views/stock_picking_views.xml',
        'views/negative_stock_report_views.xml',
        'views/menu_views.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': '_nns_post_init_enable',
}
