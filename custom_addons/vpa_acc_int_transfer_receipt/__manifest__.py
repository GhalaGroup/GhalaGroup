# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA Internal Transfer - Receipt Control',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Receipt confirmation workflow for internal transfers (v1.0.0)',
    'description': """
VPA Internal Transfer - Receipt Control
=======================================

Add-on module for VPA Accounting Internal Transfer that adds receiver-focused
cash control with custodian confirmation workflow.

Key Features
------------
* **Receipt Confirmation**: Custodians must confirm receipt before journal entries are created
* **Journal Custodians**: Assign primary and backup custodians to each bank/cash account
* **Dispute Handling**: Receivers can raise disputes with resolution workflow
* **Reassignment**: Transfer Managers can reassign pending transfers to different custodians
* **Audit Trail**: Complete tracking of all confirmations and disputes

New Workflow States
-------------------
* **Pending Receipt**: Awaiting custodian confirmation after approval
* **Received**: Both parties confirmed, journal entries created
* **Disputed**: Receiver raised an issue requiring resolution

Permission Hierarchy
--------------------
1. Primary Custodian(s) of destination journal
2. Backup Manager(s) of destination journal
3. Transfer Managers (emergency fallback)

Version History
---------------
* **19.0.1.0.0** - Initial release for Odoo 19

Requires: VPA Accounting Internal Transfer (base module)

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
        'vpa_acc_int_transfer',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/journal_custodian_views.xml',
        'views/wizard_views.xml',
        'views/internal_transfer_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu_views.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
