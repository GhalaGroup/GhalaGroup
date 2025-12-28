# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA Internal Transfer - Document Layout',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Integrates Internal Transfer reports with VPA Document Layout (v1.0.0)',
    'description': """
VPA Internal Transfer - Document Layout Integration
====================================================

This bridge module automatically integrates VPA Accounting Internal Transfer
with VPA Document Layout.

When both modules are installed, this module:
- Removes Odoo's default header/footer from Internal Transfer reports
- Applies VPA Document Layout's universal header/footer
- Uses VPA's configured colors and styling

Key Features
------------
* **Auto-Install**: Installs automatically when dependencies are present
* **VPA Styling**: Left border accent design, amount badges, status badges
* **Professional Layout**: Consistent branding across all VPA reports
* **Company Colors**: Inherits colors from VPA Document Layout config

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
    'depends': [
        'vpa_acc_int_transfer',
        'vpa_document_layout',
    ],
    'data': [
        'views/report_override.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'auto_install': True,
}
