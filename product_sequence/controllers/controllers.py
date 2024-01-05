# -*- coding: utf-8 -*-
# from odoo import http


# class ProductSequence(http.Controller):
#     @http.route('/product_sequence/product_sequence', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/product_sequence/product_sequence/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('product_sequence.listing', {
#             'root': '/product_sequence/product_sequence',
#             'objects': http.request.env['product_sequence.product_sequence'].search([]),
#         })

#     @http.route('/product_sequence/product_sequence/objects/<model("product_sequence.product_sequence"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('product_sequence.object', {
#             'object': obj
#         })
