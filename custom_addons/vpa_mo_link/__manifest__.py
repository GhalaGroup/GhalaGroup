# -*- coding: utf-8 -*-
{
    'name': 'VPA - Manufacturing Order Link',
    'version': '1.0',
    'category': 'Manufacturing',
    'summary': 'Compatibility module for Manufacturing Order automation',
    'description': """
VPA - Manufacturing Order Link
===============================

This module provides compatibility for automations that create Manufacturing Orders
from Sales Orders. It adds the procurement_group_id field to sale.order when the
stock/mrp modules are not installed, preventing AttributeError.

Features:
---------
* Adds dummy procurement_group_id field to prevent automation errors
* Allows automations to check procurement_group_id without crashing
* Compatible with Preview button and portal access

This is a separate module from VPA Document Layout to keep concerns separated.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['sale'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
