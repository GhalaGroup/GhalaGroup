# -*- coding: utf-8 -*-
"""
    This model is used to create a product line fields like product template id,website id and label
"""

from odoo import api, fields, models
from odoo.osv import expression

class ProductLabelLine(models.Model):
    _name = "product.label.line"
    _description = 'Product Template Label Line'

    product_tmpl_id = fields.Many2one('product.template', string='Product Template Id',required=True)
    website_id = fields.Many2one('website',string="Website",required=True)
    label = fields.Many2one('product.label',required=True,string="Label",help="Name of the product label")
    _sql_constraints = [('product_tmpl_id', 'unique (product_tmpl_id,website_id)',
                         'Duplicate records in label line not allowed !')]

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            args = args or []
            domain = [('label', operator, name)]
            return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return super(ProductLabelLine, self)._name_search(name=name, args=args, operator=operator,
                                                          limit=limit, name_get_uid=name_get_uid)