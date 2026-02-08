# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    commission_production_enabled = fields.Boolean(
        string='Enable Production Commission',
        config_parameter='vpa_sales_commission.production_enabled',
        default=True,
        help='Enable commission calculation based on Manufacturing Orders',
    )
    commission_sales_enabled = fields.Boolean(
        string='Enable Sales Commission',
        config_parameter='vpa_sales_commission.sales_enabled',
        default=False,
        help='Enable commission calculation based on Sales Orders (Phase 2)',
    )
    commission_auto_create = fields.Boolean(
        string='Auto-create Commission on MO Done',
        config_parameter='vpa_sales_commission.auto_create',
        default=True,
        help='Automatically create commission lines when Manufacturing Orders are completed',
    )
