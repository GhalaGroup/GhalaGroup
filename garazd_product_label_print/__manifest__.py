# Copyright © 2023 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/15.0/legal/licenses.html).

{
    'name': 'Product Label Printing without download',
    'version': '16.0.1.1.0',
    'category': 'Hidden',
    'author': 'Garazd Creation',
    'website': 'https://garazd.biz/shop',
    'license': 'OPL-1',
    'summary': 'Product Label Printing without download',
    'depends': [
        'garazd_product_label',
    ],
    'data': [
        'views/print_product_label_templates.xml',
        'wizard/print_product_label_views.xml',
    ],
    'support': 'support@garazd.biz',
    'application': False,
    'installable': True,
    'auto_install': False,
}
