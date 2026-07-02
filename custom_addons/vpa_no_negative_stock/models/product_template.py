# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    nns_allow_negative = fields.Boolean(
        string='Allow Negative Stock',
        help='Allow this product to go negative, bypassing VPA Stock Sentinel.',
    )
