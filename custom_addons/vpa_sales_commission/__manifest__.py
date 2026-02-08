# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA Production Commission',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing/Commission',
    'summary': 'Production commission based on Manufacturing Orders (v1.0.0)',
    'description': """
VPA Production Commission
=========================

Commission management system based on Manufacturing Order completion.
Commission is calculated from commissionable raw materials consumed during production.

Key Features
------------
* **Per-Employee Schemes**: Each employee has individual commission rates and minimum guarantees
* **MO-Based Commission**: Automatic calculation when Manufacturing Orders are completed
* **Commissionable Products**: Mark specific raw materials to be included in commission calculation
* **MO Filtering**: Configure which MOs apply per scheme (all, workcenter, category, products)
* **Minimum Guarantee**: Annual minimum with monthly/quarterly tracking
* **Approval Workflow**: Pending -> Confirmed -> Paid status tracking
* **High Security**: Strict access control - Commission Managers only
* **Search Panel**: Side panel with Status and Employee filters
* **Pivot & Graph Views**: Export to Excel, visual commission analysis
* **User Access Rights**: Privilege-based access in User form

Version History
---------------
* **19.0.1.0.0** - Initial release for Odoo 19
  - Per-employee commission schemes
  - Production commission on MO completion
  - Commissionable product flag
  - Configurable MO filters
  - Minimum guarantee system
  - Approval workflow
  - Search panel with Status and Employee filters
  - Pivot view for commission analysis with Excel export
  - Graph view for visual reporting
  - Privilege-based user access (Sales Commission section in user form)
  - Date filter with year/month/quarter selection

Developed by VPA Solutions Limited
Support: info@vpa.co.tz
    """,
    'author': 'VPA Solutions Limited',
    'website': 'https://www.vpa.co.tz',
    'support': 'info@vpa.co.tz',
    'license': 'OPL-1',
    'price': 299.00,
    'currency': 'USD',
    'depends': [
        'mrp',
        'hr',
        'sale',
        'sale_mrp',
        'account',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'wizard/commission_generate_wizard_views.xml',
        'wizard/commission_payment_wizard_views.xml',
        'wizard/commission_statement_wizard_views.xml',
        'report/commission_statement_report.xml',
        'report/commission_statement_template.xml',
        'views/vpa_commission_scheme_views.xml',
        'views/vpa_commission_line_views.xml',
        'views/product_template_views.xml',
        'views/mrp_production_views.xml',
        'views/hr_employee_views.xml',
        'views/res_config_settings_views.xml',
        'views/vpa_commission_guarantee_views.xml',
        'views/menuitems.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
