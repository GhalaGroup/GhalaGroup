# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA Production Studio - Configurator',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Product configurator with dimension-based pricing for variable-sized items (v1.0.0)',
    'description': """
VPA Production Studio - Configurator
=====================================

Full product configurator for quoting variable-sized items with configurable options.
Products like doors, cabinets, wall cladding get dimension-based pricing with
product-linked configuration variables.

Key Features
------------
* **Dimension Templates**: Reusable configuration schemas (W×H, W×H×D, etc.)
* **Configuration Variables**: Simple text selections or inventory-product-linked options
* **Formula-Based Pricing**: Rate per m2/m3/linear m with surcharges
* **Display Groups**: Organize variables into named sections (Door Leaf, Frame, Hardware)
* **Configurator Popup**: Live price preview while entering dimensions and options
* **Clean Quotations**: Customer sees specs + total price, no rate/surcharge breakdown
* **MO Integration**: Dimensions and config flow to manufacturing with spec panel
* **BOM Scaling**: Components scale by area/volume, placeholders replaced by selections
* **Excel Import**: Bulk dimension entry from spreadsheets

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
    'price': 6000.00,
    'currency': 'USD',
    'depends': [
        'vpa_production_base',
        'sale_mrp',
        'mrp',
        'sale',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/vpa_dimension_template_views.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_production_views.xml',
        'views/menu_views.xml',
        'wizard/product_configurator_wizard_views.xml',
        'wizard/dimension_import_wizard_views.xml',
        'report/dimension_template_report.xml',
        'data/vpa_dimension_template_data.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
