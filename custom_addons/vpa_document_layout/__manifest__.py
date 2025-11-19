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
        'views/vpa_menu_root.xml',        # 1. Load root menu first
        'views/vpa_template_views.xml',   # 2. Load template views (defines action_vpa_document_template)
        'views/vpa_config_views.xml',     # 3. Load config views (references action_vpa_document_template)
        'views/report_templates.xml',
        'views/preview_template.xml',
        'views/template_preview.xml',     # Template preview
        'data/report_layout.xml',
        'data/default_templates.xml',     # Default templates
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
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
