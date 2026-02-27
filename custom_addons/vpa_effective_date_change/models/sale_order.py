# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class SaleOrderEffectiveDate(models.Model):
    _inherit = "sale.order"

    date_order = fields.Datetime(tracking=True)

    def wiz_open_so(self):
        """Opens the wizard to change the order date."""
        return {
            'name': 'Change Order Date',
            'type': 'ir.actions.act_window',
            'res_model': 'change.effective.wizard.so',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_id': self.id},
        }
