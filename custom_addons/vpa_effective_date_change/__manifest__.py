# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA Effective Date Change',
    'author': 'VPA Solutions Limited',
    'version': '19.0.1.1.0',
    'summary': 'Change effective dates for stock transfers and manufacturing orders (v1.1.0)',
    'license': 'OPL-1',
    'sequence': 10,
    'description': """
VPA Effective Date Change - Professional Date Management
=========================================================

A professional solution for modifying effective dates of validated stock transfers
and manufacturing orders with automatic synchronization of all related accounting
and inventory records.

Key Features
------------
* **Stock Transfer Date Change**: Modify effective dates for validated deliveries, receipts, and internal transfers
* **Manufacturing Order Date Change**: Modify completion dates for done manufacturing orders
* **Pre-Validation Dating**: Set custom effective date before validation
* **Smart Wizard**: Intuitive interface for changing dates after validation
* **Automatic Synchronization**: Updates all related records:
  - Stock Moves & Move Lines
  - Journal Entries (Account Moves)
  - Stock Valuation Layers
  - Product Costs (FIFO & Average)
* **Multi-Currency Support**: Recalculates foreign currency purchase valuations with correct exchange rates
* **Currency Rate Validation**: Ensures exchange rates exist for selected dates
* **Access Control**: Permission-based security for authorized users only
* **Odoo 19 Ready**: Fully compatible with Odoo 19 Enterprise

Version History
---------------
* **19.0.1.1.0** - Added Manufacturing Order support
  - Change completion date for done MOs
  - Pre-set effective date before marking MO as done
  - Syncs all related stock moves and valuation layers

* **19.0.1.0.0** - Initial release
  - Stock transfer date change functionality
  - Pre-validation and post-validation dating
  - Multi-currency recalculation

Developed by VPA Solutions Limited
Support: info@vpa.co.tz
    """,
    'category': 'Inventory/Inventory',
    'website': 'https://www.vpa.co.tz',
    'support': 'info@vpa.co.tz',
    'price': 79.00,
    'currency': 'USD',
    'depends': [
        'account_accountant',
        'stock',
        'sale_management',
        'purchase',
        'mrp',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/effective_date_change.xml',
        'views/effective_date_change_privilege.xml',
        'views/mrp_production_views.xml',
        'wizard/change_effective_wizard_views.xml',
        'wizard/change_effective_wizard_mo_views.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'pre_init_hook': 'pre_init_check',
}
