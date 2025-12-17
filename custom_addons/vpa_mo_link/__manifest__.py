# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Software Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA - Manufacturing Order Link',
    'version': '19.0.1.1.0',
    'category': 'Manufacturing',
    'summary': 'Advanced Manufacturing Order management with flexible workflows and manual linking',
    'price': 199.00,
    'currency': 'USD',
    'description': """
VPA - Manufacturing Order Link
===============================

Extends Odoo's standard manufacturing integration to support custom workflows.

Key Features:
-------------
1. **Draft MO Creation**: All auto-created MOs stay in DRAFT (never auto-confirmed)
2. **No-BOM Support**: MOs created even when BOM is missing (user sets later)
3. **Manual MO Linking**: Link MOs created before Sales Orders
4. **Unified Smart Button**: Shows both automatic and manually linked MOs
5. **Manufacture - Draft MO Route**: Dedicated route that creates MOs in draft state

Workflows Supported:
--------------------
* Standard: Product with route → Confirm SO → MO in DRAFT → Review → Confirm
* No BOM: Product without BOM → Confirm SO → MO in DRAFT → Set BOM → Confirm
* Manual: Create MO → Set Source field → Create SO → MO appears in smart button
* Link Action: Create MO → Create SO → Click "MO - Link/Unlink" → Toggle link

Technical Details:
------------------
* Overrides stock_rule._should_auto_confirm_procurement_mo() to return False
* Overrides stock_rule._prepare_mo_vals() to handle missing BOMs
* Extends sale_mrp._compute_mrp_production_ids() to include origin-based MOs
* Single MO - Link/Unlink toggle action manages origin field for manual linking
* Compatible with procurement_group_id automations
* Creates "Manufacture - Draft MO" route automatically on installation

Support:
--------
For support, customization, or feature requests:
* Email: support@vpasoftware.com
* Website: https://www.vpasoftware.com

Author: VPA Software Limited
Copyright (C) 2025 VPA Software Limited
    """,
    'author': 'VPA Software Limited',
    'website': 'https://www.vpasoftware.com',
    'maintainer': 'VPA Software Limited',
    'support': 'support@vpasoftware.com',
    'images': ['static/description/icon.png'],
    'depends': ['sale_mrp', 'mrp', 'stock'],
    'data': [
        'data/stock_route_data.xml',
        'data/ir_actions_server.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',
}
