# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA Effective Date Change',
    'author': 'VPA Solutions Limited',
    'version': '19.0.1.0.0',
    'summary': 'Change stock transfer effective dates with automatic accounting synchronization',
    'license': 'OPL-1',
    'sequence': 10,
    'description': """
VPA Effective Date Change - Professional Transfer Date Management
==================================================================

A professional solution for modifying effective dates of validated stock transfers
with automatic synchronization of all related accounting and inventory records.

Key Features
------------
* **Change Transfer Dates**: Modify effective dates for validated deliveries, receipts, and internal transfers
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

Business Benefits
-----------------
* Correct backdated stock transactions
* Maintain accurate financial period reporting
* Ensure audit compliance with proper transaction dates
* Handle late-validated transfers with correct dates

Technical Features
------------------
* Safe database updates with existence checks
* Multi-currency valuation recalculation
* Comprehensive date synchronization
* User permission management

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
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/effective_date_change.xml',
        'views/effective_date_change_privilege.xml',
        'wizard/change_effective_wizard_views.xml',
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
