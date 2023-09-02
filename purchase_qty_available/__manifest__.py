# -*- coding: utf-8 -*-
{
    'name': "Purchase Qty Available",

    'summary': """
       Show quantity on hand in purchase order line.""",

    'description': """
        Show quantity on hand in purchase order line.
    """,

    'author': "StiloTech Limited",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Purchase',
    'version': '14.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase','stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
