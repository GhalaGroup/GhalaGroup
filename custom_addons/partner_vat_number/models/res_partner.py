# -*- coding: utf-8 -*-

from odoo import models, fields, api, _ 
from odoo.exceptions import  ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.constrains('journal_id', 'move_type')
    def _check_journal_move_type(self):
        for move in self:
            if move.is_purchase_document(include_receipts=True) and move.journal_id.type != 'purchase':
                currency = move.invoice_line_ids[0].currency_id if move.invoice_line_ids else move.currency_id
                journal_id = self.env['account.journal'].search([
                    ('type','=','purchase'),
                    ('currency_id','=',currency.id),
                ],limit=1)
                move.journal_id = journal_id.id
                #raise ValidationError(_("Cannot create a purchase document in a non purchase journal"))
            if move.is_sale_document(include_receipts=True) and move.journal_id.type != 'sale':
                raise ValidationError(_("Cannot create a sale document in a non sale journal"))

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
