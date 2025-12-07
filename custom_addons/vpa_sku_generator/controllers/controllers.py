# -*- coding: utf-8 -*-
# from odoo import http


# class ProductSequence(http.Controller):
#     @http.route('/vpa_sku_generator/vpa_sku_generator', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/vpa_sku_generator/vpa_sku_generator/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('vpa_sku_generator.listing', {
#             'root': '/vpa_sku_generator/vpa_sku_generator',
#             'objects': http.request.env['vpa_sku_generator.vpa_sku_generator'].search([]),
#         })

#     @http.route('/vpa_sku_generator/vpa_sku_generator/objects/<model("vpa_sku_generator.vpa_sku_generator"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('vpa_sku_generator.object', {
#             'object': obj
#         })
