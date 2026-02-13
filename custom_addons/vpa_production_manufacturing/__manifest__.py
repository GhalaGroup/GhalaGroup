# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA Production Studio - Manufacturing',
    'version': '19.0.1.1.0',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Manufacturing Orders with Template BOM Support (v1.1.0)',
    'description': """
VPA Production Manufacturing
============================

Module 6 of VPA Production Studio - Manufacturing Orders with Template BOM Support.

Key Features
------------
* **Template Line Support**: Create MOs from Master BOMs with category-based template lines
* **Product Selection**: Workers select actual products from category-filtered dropdown
* **Variance Tracking**: Track Master BOM Qty vs Physical Qty Used with auto-calculated variance
* **Flexible Workflow**: Select products before confirmation or during production
* **Validation**: MO cannot be completed until all template lines have actual products
* **Master BOMs Menu**: Dedicated menu with searchpanel for STATUS and PRODUCT CATEGORY filtering

Variance Tracking Columns
-------------------------
* Master BOM Qty - Original quantity from Master BOM template
* Physical Qty Used - Actual quantity entered by worker
* Variance - Difference (Physical - Master)

Version History
---------------
* **19.0.1.1.0** - Enhanced Master BOMs menu with searchpanel (status/category filtering)
* **19.0.1.0.0** - Initial release with variance tracking and template line support

Developed by VPA Solutions Limited
Support: info@vpa.co.tz
    """,
    'author': 'VPA Solutions Limited',
    'website': 'https://www.vpa.co.tz',
    'support': 'info@vpa.co.tz',
    'license': 'OPL-1',
    'price': 8000.00,
    'currency': 'USD',
    'depends': [
        'vpa_production_base',
        'mrp',
        'stock',
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_bom_views.xml',
        'views/mrp_production_views.xml',
        'views/sale_order_views.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
