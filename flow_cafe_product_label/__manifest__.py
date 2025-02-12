# -*- coding: utf-8 -*-
{
    'name': "Flow Cafe Product Label",

    'summary': """
        Customised the dymo product label. 
        """,

    'description': """
        Added customised dymo product label as per client requirements which show Barcodes, 
        Internal Reference codes, Name of products, Quantity, etc., 
        Also customised standard size of dymo to 80mm*80mm. 
    """,

    'author': "Hayagreeva Kasibhotla",
    'website': "https://www.byteeit.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'LearningSpace',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product'],

    # always loaded
    'data': [
        'data/custom_dymo_label_size.xml',
        'reports/custom_dymo_product_label.xml',

    ],

}
