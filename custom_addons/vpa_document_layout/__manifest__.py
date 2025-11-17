# -*- coding: utf-8 -*-
{
    'name': 'VPA Document Layout',
    'version': '1.0.0',
    'category': 'Reporting',
    'summary': 'Custom VPA document layout for reports',
    'description': """
        VPA Document Layout
        ===================
        Custom document layout based on modern styling with full customization.
        Features table styling and custom header/footer design.

        PDF Engine: WeasyPrint for superior CSS rendering
    """,
    'author': 'VPA',
    'website': '',
    'depends': ['web', 'base_setup', 'sale', 'account'],
    # WeasyPrint is optional - will fall back to wkhtmltopdf if not available
    # 'external_dependencies': {
    #     'python': ['weasyprint'],
    # },
    'data': [
        'security/ir.model.access.csv',
        'views/vpa_config_views.xml',
        'views/menu_workaround.xml',
        'views/report_templates.xml',
        'views/preview_template.xml',
        'data/report_layout.xml',
        'views/sale_order_report_inherit.xml',
        'views/account_invoice_report_inherit.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
