# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA Document Layout',
    'version': '19.0.1.2.0',
    'category': 'Reporting',
    'summary': 'Custom VPA document layout for reports (v19.0.1.2.0)',
    'description': """
VPA Document Layout
===================

Professional custom document layout for Odoo 19 Enterprise reports.

Key Features
------------
* **Multiple Templates**: Support for various report templates (Standard, Modern, Quotation Pictures)
* **Custom Header/Footer**: Fully customizable header and footer design
* **Table Styling**: Professional table styling with gradient backgrounds and accent borders
* **Logo Integration**: Company logo support with proper sizing and positioning
* **PDF Engine**: WeasyPrint support for superior CSS rendering (with wkhtmltopdf fallback)
* **Template Preview**: Live preview of templates before applying
* **Multi-Company**: Full multi-company support
* **Backup/Restore**: Automatic backup before uninstall, restore wizard after reinstall

Supported Reports
-----------------
* Sale Orders / Quotations
* Invoices / Credit Notes
* Manufacturing Orders

Version History
---------------
* **19.0.1.2.0** - Header spacing fix, Quotation Pictures table styling, product image border removed
* **19.0.1.1.0** - Added template preview, header repeat on pages option
* **19.0.1.0.0** - Initial release for Odoo 19

Developed by VPA Solutions Limited
Support: info@vpa.co.tz
    """,
    'author': 'VPA Solutions Limited',
    'website': 'https://www.vpa.co.tz',
    'support': 'info@vpa.co.tz',
    'license': 'OPL-1',
    'price': 79.99,
    'currency': 'USD',
    'depends': ['web', 'base_setup', 'sale', 'account', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/vpa_menu_root.xml',
        'views/vpa_template_views.xml',
        'views/vpa_config_views.xml',
        'views/vpa_footer_config_views.xml',
        'views/vpa_backup_views.xml',
        'views/report_templates.xml',
        'views/preview_template.xml',
        'views/template_preview.xml',
        'views/template_preview_fullpage.xml',
        'views/vpa_footer_only.xml',
        'views/vpa_footer_preview.xml',
        'views/vpa_footer_unified.xml',
        'views/vpa_footer_override.xml',
        'wizard/import_footer_wizard_views.xml',
        'data/report_layout.xml',
        'data/default_templates.xml',
        'data/default_footers.xml',
        'views/sale_order_report_inherit.xml',
        'views/account_invoice_report_inherit.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'vpa_document_layout/static/src/scss/vpa_document_layout.scss',
            'vpa_document_layout/static/src/js/vpa_preview_widget.js',
            'vpa_document_layout/static/src/xml/vpa_preview_widget.xml',
        ],
    },
    'images': [
        'static/description/icon.png',
    ],
    'post_init_hook': '_post_init_hook',
    'uninstall_hook': '_uninstall_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
