# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA Accounting Internal Transfer',
    'version': '19.0.1.2.0',
    'category': 'Accounting/Accounting',
    'summary': 'Internal fund transfers with multi-level approval workflow',
    'description': """
VPA Accounting Internal Transfer
================================

Professional internal fund transfer management for Odoo 19 Enterprise.

Key Features
------------
* **Internal Transfers**: Bank-to-bank, bank-to-cash, cash-to-bank, cash-to-cash transfers
* **Multi-Level Approval**: Threshold-based approval routing (Manager/Admin)
* **Journal Entries**: Automatic journal entry creation with detailed remarks
* **Auto-Reconciliation**: Automatic reconciliation of transfer account entries
* **Audit Trail**: Complete tracking via chatter (mail.thread)
* **Multi-Currency**: Support for transfers between different currency accounts
* **Multi-Company**: Full multi-company support
* **Cancellation Workflow**: Proper reversal entries on cancellation
* **PDF Reports**: Professional transfer voucher printout
* **Backup/Restore**: Automatic backup before uninstall, restore wizard after reinstall

Security Roles (Uses Standard Odoo Groups)
------------------------------------------
* **Accountant (group_account_user)**: Create and submit transfers
* **Account Manager (group_account_manager)**: Approve, reject, cancel transfers and configure settings

Dashboard Views
---------------
* All Transfers
* Pending Approvals
* Rejected Transfers
* Posted Transfers

Developed by VPA Solutions Limited
Support: info@vpa.co.tz
    """,
    'author': 'VPA Solutions Limited',
    'website': 'https://www.vpa.co.tz',
    'license': 'OPL-1',
    'price': 199.00,
    'currency': 'USD',
    'depends': [
        'account_accountant',
        'mail',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/approval_threshold_data.xml',
        'report/transfer_report.xml',
        'report/transfer_report_template.xml',
        'wizard/transfer_wizard_views.xml',
        'views/internal_transfer_views.xml',
        'views/approval_threshold_views.xml',
        'views/res_config_settings_views.xml',
        'views/backup_views.xml',
        'views/menu_views.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'uninstall_hook': 'pre_uninstall_hook',
    'post_init_hook': 'post_init_hook',
}
