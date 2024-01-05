# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _sql_constraints = [
        ("vrn_uniq", "unique (vrn)", "VAT must be unique!"),
        ("vat_uniq", "unique (vat)", "TIN must be unique!"),
    ]
    vat = fields.Char(string='TIN Number')
    vrn = fields.Char(string='VAT Number', copy=False)

# class partner-vat-number(models.Model):
#     _name = 'partner-vat-number.partner-vat-number'
#     _description = 'partner-vat-number.partner-vat-number'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
