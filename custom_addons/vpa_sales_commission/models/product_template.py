# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    not_commissionable = fields.Boolean(
        string='Not Commissionable',
        default=False,
        groups='vpa_sales_commission.group_commission_manager',
        help='If checked, this product will be excluded from commission calculations '
             'when used as a raw material in Manufacturing Orders.',
    )
