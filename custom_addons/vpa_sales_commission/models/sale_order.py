# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('name', 'client_order_ref', 'partner_id')
    def _compute_display_name(self):
        super()._compute_display_name()
        for order in self:
            if order.client_order_ref:
                order.display_name = '%s · %s' % (order.name, order.client_order_ref)
