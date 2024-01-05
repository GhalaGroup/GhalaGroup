# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    mrp_note = fields.Text('Note')

    product_description_variants = fields.Char(string="Custom Description", compute="_compute_sol_name", store=True, inverse="_inverse_compute_sol_name")

    @api.depends('procurement_group_id')
    def _compute_sol_name(self):
        for record in self:
            if record.origin:
                sale_order = record.env['sale.order'].search([('name', '=', record.origin)])
                if sale_order and sale_order.order_line.name:
                    record['product_description_variants'] = sale_order.order_line.name


    def _inverse_compute_sol_name(self):
        for record in self:
            if record.origin:
                sale_order = record.env['sale.order'].search([('name', '=', record.origin)])
                if sale_order and sale_order.order_line.name:
                    record['product_description_variants'] = sale_order.order_line.name
                else:
                    record['product_description_variants'] = ""



#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
