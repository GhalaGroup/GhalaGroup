# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderLineConfig(models.Model):
    _name = 'sale.order.line.config'
    _description = 'Sale Order Line Configuration Value'

    sale_line_id = fields.Many2one('sale.order.line', string='Sale Line',
                                   required=True, ondelete='cascade')
    variable_id = fields.Many2one('vpa.config.variable', string='Variable',
                                  required=True, ondelete='restrict')
    option_id = fields.Many2one('vpa.config.variable.option', string='Selected Option',
                                required=True, ondelete='restrict')
    product_id = fields.Many2one('product.product', string='Selected Product',
                                 related='option_id.product_id', store=True)
