# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('name', 'partner_id.name', 'client_order_ref')
    def _compute_display_name(self):
        if not self.env.context.get('sale_show_partner_name'):
            return super()._compute_display_name()
        for order in self:
            name = order.name
            if order.partner_id.name:
                name = f'{name} - {order.partner_id.name}'
            if order.client_order_ref:
                name = f'{name} ({order.client_order_ref})'
            order.display_name = name
