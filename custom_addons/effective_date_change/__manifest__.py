# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Change Effective Date',
    'author': 'VPA Software Limited',
    'version': '1.0.1',
    'summary': 'Modify Transfer Effective Dates with Automatic Accounting & Valuation Updates',
    'license': 'OPL-1',
    'sequence': 1,
    'description': """
Change Effective Date - Complete Transfer Date Management
==========================================================

A professional tool that allows you to change the effective date of stock transfers (Delivery Orders, Receipts, Internal Transfers)
with automatic synchronization of all related accounting entries and inventory valuations.

Key Features
------------
* **Change Transfer Dates**: Modify effective dates for validated stock pickings
* **View Original Date**: See the current effective date before making changes
* **Smart Wizard**: Clean, intuitive interface for date selection
* **Automatic Updates**: Synchronizes dates across:
  - Stock Moves & Move Lines
  - Account Moves & Journal Entries
  - Stock Valuation Layers
  - Product Costs (FIFO & Average)
* **Multi-Currency Support**: Recalculates valuations with correct exchange rates for foreign currency purchases
* **Journal Entry Renaming**: Automatically updates journal entry sequences when changing dates
* **Permission Control**: Security groups to control who can change effective dates
* **Odoo 19 Compatible**: Fully tested and optimized for Odoo 19 Enterprise

Use Cases
---------
* Correct backdated receipts or deliveries
* Adjust inventory transfer dates for reporting accuracy
* Fix timing issues in financial closing periods
* Update transfer dates for audit compliance

Developer: VPA Software Limited
Support: Professional-grade support available
    """,
    'category': 'Inventory/Inventory',
    'website': 'https://www.vpasoftware.com',
    'price': 49.99,
    'currency':'USD',
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
        'static/description/assets/banner.gif',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'pre_init_hook': 'pre_init_check',
}
