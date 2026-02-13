# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_import_dimensions(self):
        """Open the dimension import wizard."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Import Dimensions',
            'res_model': 'vpa.dimension.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_id': self.id},
        }
