# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    total_purchase_product = fields.Integer(string='Total Products:',compute='_total_purchase_product',help="total Products")
    total_purchase_quantity = fields.Integer(string='Total Quantities:',compute='_total_purchase_product_qty',help="total Quantity")

    def _total_purchase_product(self):
        for record in self:
            list_of_product=[]
            for line in record.order_line:
                list_of_product.append(line.product_id)
            record.total_purchase_product = len(set(list_of_product))

    def _total_purchase_product_qty(self):
        for record in self:
            total_qty = 0
            for line in record.order_line:
                total_qty = total_qty + line.product_qty
            record.total_purchase_quantity = total_qty
