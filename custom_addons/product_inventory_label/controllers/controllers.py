# -*- coding: utf-8 -*-
# from odoo import http


# class ProductInventoryLabel(http.Controller):
#     @http.route('/product_inventory_label/product_inventory_label', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/product_inventory_label/product_inventory_label/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('product_inventory_label.listing', {
#             'root': '/product_inventory_label/product_inventory_label',
#             'objects': http.request.env['product_inventory_label.product_inventory_label'].search([]),
#         })

#     @http.route('/product_inventory_label/product_inventory_label/objects/<model("product_inventory_label.product_inventory_label"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('product_inventory_label.object', {
#             'object': obj
#         })
