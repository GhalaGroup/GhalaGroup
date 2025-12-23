# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA Internal Transfer - Document Layout',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Integrates Internal Transfer reports with VPA Document Layout',
    'description': """
VPA Internal Transfer - Document Layout Integration
====================================================

This bridge module automatically integrates VPA Accounting Internal Transfer
with VPA Document Layout.

When both modules are installed, this module:
- Removes Odoo's default header/footer from Internal Transfer reports
- Applies VPA Document Layout's universal header/footer
- Uses VPA's configured colors and styling

This module auto-installs when both dependencies are present.
No manual installation required.

Developed by VPA Solutions Limited
Support: info@vpa.co.tz
    """,
    'author': 'VPA Solutions Limited',
    'website': 'https://www.vpa.co.tz',
    'license': 'OPL-1',
    'depends': [
        'vpa_acc_int_transfer',
        'vpa_document_layout',
    ],
    'data': [
        'views/report_override.xml',
    ],
    'installable': True,
    'auto_install': True,
}
