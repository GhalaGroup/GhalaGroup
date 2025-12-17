# -*- coding: utf-8 -*-
{
    'name': 'VPA Document Layout',
    'version': '19.0.1.1.1',
    'category': 'Reporting',
    'summary': 'Custom VPA document layout for reports',
    'description': """
        VPA Document Layout
        ===================
        Custom document layout based on modern styling with full customization.
        Features table styling and custom header/footer design.

        PDF Engine: WeasyPrint for superior CSS rendering
    """,
    'author': 'VPA Software Limited',
    'website': 'https://www.vpasoftware.com',
    'support': 'support@vpasoftware.com',
    'license': 'OPL-1',
    'price': 79.99,
    'currency': 'USD',
    'depends': ['web', 'base_setup', 'sale', 'account', 'mrp'],
    # WeasyPrint is optional - will fall back to wkhtmltopdf if not available
    # 'external_dependencies': {
    #     'python': ['weasyprint'],
    # },
    'data': [
        'security/ir.model.access.csv',
        'views/vpa_menu_root.xml',        # 1. Load root menu first
        'views/vpa_template_views.xml',   # 2. Load template views (defines action_vpa_document_template)
        'views/vpa_config_views.xml',     # 3. Load config views (references action_vpa_document_template)
        'views/vpa_footer_config_views.xml',  # 4. Footer config views and menu
        'views/vpa_backup_views.xml',         # 5. Backup/restore views and menu
        'views/report_templates.xml',
        'views/preview_template.xml',
        'views/template_preview.xml',     # Template preview
        'views/template_preview_fullpage.xml',  # Full page preview
        'views/vpa_footer_only.xml',      # Footer-only template for wkhtmltopdf --footer-html
        'views/vpa_footer_preview.xml',   # Footer preview page
        'views/vpa_footer_unified.xml',   # Unified footer templates
        'views/vpa_footer_override.xml',  # Override Odoo standard layouts
        'data/report_layout.xml',
        'data/default_templates.xml',     # Default templates
        'data/default_footers.xml',       # Default footer configs
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
    'post_init_hook': '_post_init_hook',
    'uninstall_hook': '_uninstall_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
