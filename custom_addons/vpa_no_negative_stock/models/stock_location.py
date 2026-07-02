# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    nns_allow_negative = fields.Boolean(
        string='Allow Negative Stock',
        help='Allow stock at this location to go negative, bypassing VPA Stock '
             'Sentinel.',
    )
