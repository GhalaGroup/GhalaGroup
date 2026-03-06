# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA Label Designer',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Design & print ZPL labels to Zebra printers (v1.0.0)',
    'description': """
VPA Label Designer
==================

Professional label design and printing for Zebra thermal printers in Odoo 19 Enterprise.

Key Features
------------
* **Label Size Management**: Create custom label sizes (mm to dots conversion) with RFID support
* **Template Designer**: Form-based label template designer with text, barcodes, QR codes, variables, lines, boxes, and images
* **ZPL Engine**: Generates Zebra Programming Language (ZPL II) code for each label element
* **Variable System**: Dynamic field resolution using dot-notation paths (e.g., product_id.categ_id.name)
* **Live Preview**: Visual label preview via Labelary API integration
* **Direct Network Printing**: Send ZPL directly to Zebra printers via TCP socket (port 9100)
* **Zebra Browser Print**: Client-side printing via Zebra Browser Print SDK (localhost:9101)
* **Purchase Order Integration**: Print labels with quantities from PO lines, editable before printing
* **Alternative UoM Support**: Switch label UoM using VPA UoM alternative conversions
* **RFID Support**: EPC Gen2 / UHF RFID tag encoding via ^RFW command
* **Multi-Source Printing**: Print from Products, Purchase Orders, Manufacturing Orders, Stock Pickings, Lots
* **Multi-Company**: Full multi-company support with record rules

Version History
---------------
* **19.0.1.0.0** - Initial release for Odoo 19

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
        'product',
        'stock',
        'purchase',
        'mrp',
        'mail',
        'vpa_uom',
    ],
    'data': [
        'security/label_designer_security.xml',
        'security/ir.model.access.csv',
        'data/label_variable_data.xml',
        'views/label_size_views.xml',
        'views/label_template_views.xml',
        'views/label_element_views.xml',
        'views/printer_config_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_users_views.xml',
        'wizard/print_label_wizard_views.xml',
        'wizard/import_label_wizard_views.xml',
        'wizard/copy_elements_wizard_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'vpa_label_designer.konva_lib': [
            'vpa_label_designer/static/lib/konva/konva.min.js',
        ],
        'web.assets_backend': [
            'vpa_label_designer/static/lib/konva/konva.min.js',
            'vpa_label_designer/static/src/js/canvas/font_metrics.js',
            'vpa_label_designer/static/src/js/canvas/grid_layer.js',
            'vpa_label_designer/static/src/js/canvas/element_factory.js',
            'vpa_label_designer/static/src/js/label_canvas_editor.js',
            'vpa_label_designer/static/src/js/label_preview_widget.js',
            'vpa_label_designer/static/src/js/zebra_print.js',
            'vpa_label_designer/static/src/xml/label_canvas_editor.xml',
            'vpa_label_designer/static/src/xml/label_preview_widget.xml',
            'vpa_label_designer/static/src/scss/label_designer.scss',
        ],
    },
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
