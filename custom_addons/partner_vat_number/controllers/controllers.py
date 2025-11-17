# -*- coding: utf-8 -*-
# from odoo import http


# class Partner-vat-number(http.Controller):
#     @http.route('/partner-vat-number/partner-vat-number', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/partner-vat-number/partner-vat-number/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('partner-vat-number.listing', {
#             'root': '/partner-vat-number/partner-vat-number',
#             'objects': http.request.env['partner-vat-number.partner-vat-number'].search([]),
#         })

#     @http.route('/partner-vat-number/partner-vat-number/objects/<model("partner-vat-number.partner-vat-number"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('partner-vat-number.object', {
#             'object': obj
#         })
