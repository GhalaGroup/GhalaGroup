# -*- coding: utf-8 -*-


{
    'name': "Total Number Of Products And Quantity On RFQ / Purchase Order",
    'author': 'Stephen Ngailo',
    'category': 'Purchases',
    'summary': """Display Total Number Of Products And Quantity On RFQ / Purchase Order""",
    'description': """
""",
    'version': '14.0.0.1',
    'depends': ['base','purchase'],
    'data': ['security/purchase_order_security.xml',
             'views/purchase_order_view.xml',
             'report/purchase_report_templates.xml',
             'report/purchase_quotation_templates.xml'],
  
    'installable': True,
    'application': True,
    'auto_install': False,
}




