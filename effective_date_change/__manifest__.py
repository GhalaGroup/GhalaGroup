# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Change Effective Date',
    'author': 'Altela Software',
    'version': '16.0.8.6.1',
    'summary': 'Change Effective Date in Stock Picking',
    'license': 'OPL-1',
    'sequence': 1,
    'description': """Allows You Changing Effective Date of DO, RO, Internal and All Inventory Transfers""",
    'category': 'Inventory',
    'website': 'https://www.altelasoftware.com',
    'price':'40',
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
