# -*- coding: utf-8 -*-
# from odoo import http


# class MrpProductDescriptionVariant(http.Controller):
#     @http.route('/mrp_product_description_variant/mrp_product_description_variant', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mrp_product_description_variant/mrp_product_description_variant/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('mrp_product_description_variant.listing', {
#             'root': '/mrp_product_description_variant/mrp_product_description_variant',
#             'objects': http.request.env['mrp_product_description_variant.mrp_product_description_variant'].search([]),
#         })

#     @http.route('/mrp_product_description_variant/mrp_product_description_variant/objects/<model("mrp_product_description_variant.mrp_product_description_variant"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mrp_product_description_variant.object', {
#             'object': obj
#         })
