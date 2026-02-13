# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderLineDimension(models.Model):
    _name = 'sale.order.line.dimension'
    _description = 'Sale Order Line Dimension Value'

    sale_line_id = fields.Many2one('sale.order.line', string='Sale Line',
                                   required=True, ondelete='cascade')
    dimension_line_id = fields.Many2one('vpa.dimension.template.line', string='Dimension',
                                        required=True, ondelete='restrict')
    value = fields.Float(string='Value', required=True)
