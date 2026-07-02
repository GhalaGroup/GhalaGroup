# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    nns_allow_negative = fields.Boolean(
        string='Allow Negative Stock',
        help='Allow products in this category (and its child categories) to go '
             'negative, bypassing VPA Stock Sentinel.',
    )

    def _nns_allows_negative(self):
        """Return True if this category or any parent category allows negatives."""
        category = self
        while category:
            if category.nns_allow_negative:
                return True
            category = category.parent_id
        return False
