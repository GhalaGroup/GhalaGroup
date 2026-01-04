# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA Production Studio - Base',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Master BOM with Categories & Material Selection (v1.0.0)',
    'description': """
VPA Production Studio - Base
============================

Foundation module for VPA Production Studio implementing Master BOM
with BOM Categories (similar to SAP BOM Groups).

Key Features
------------
* **BOM Categories**: Classify raw materials (Paint, Hardwood, Hinges, etc.)
* **Raw Material Flag**: Mark products as raw materials with category assignment
* **Master BOM Template**: Create BOMs with Category + Description + Qty (no specific product)
* **BOM Manager Security**: Only authorized users can create/edit BOMs
* **Cost Visibility Control**: Hide costs from non-Accounting users
* **Full Audit Trail**: Track all BOM changes with timestamps and users

Workflow
--------
1. Admin creates BOM Categories (Paint, Hardwood, Hinges, etc.)
2. Products marked as "Raw Material" with assigned categories
3. Master BOM created with Category + Description + UoM + Qty
4. Workers select actual products from filtered category dropdown in MO

Part 1 of 4 - VPA Production Studio Suite
-----------------------------------------
* Part 1: Core BOM & Categories (this module)
* Part 2: MO Material Selection (visual catalogue, variance tracking)
* Part 3: Dimension Pricing (historical costs, quote integration)
* Part 4: Commission Module (separate vpa_commission app)

Version History
---------------
* **19.0.1.0.0** - Initial release with BOM Categories and Master BOM

Developed by VPA Solutions Limited
Support: info@vpa.co.tz
    """,
    'author': 'VPA Solutions Limited',
    'website': 'https://www.vpa.co.tz',
    'support': 'info@vpa.co.tz',
    'license': 'OPL-1',
    'price': 2000.00,
    'currency': 'USD',
    'depends': [
        'mrp',
        'product',
        'stock',
        'account',
    ],
    'data': [
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/vpa_bom_category_data.xml',
        # Reports
        'report/mrp_bom_structure_inherit.xml',
        # Views
        'views/vpa_bom_category_views.xml',
        'views/product_template_views.xml',
        'views/mrp_bom_views.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
