# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = "product.category"
    short_name = fields.Char(string="Category Short Name", required=True)
    company_id = fields.Many2one('res.company', required=True
)

