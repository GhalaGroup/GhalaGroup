# -*- coding: utf-8 -*-
from odoo import api, fields, models


class VpaConfigVariableOption(models.Model):
    _name = 'vpa.config.variable.option'
    _description = 'Configuration Variable Option'
    _order = 'sequence, id'

    variable_id = fields.Many2one('vpa.config.variable', string='Variable',
                                  required=True, ondelete='cascade')
    name = fields.Char(string='Option Label', required=True, help='e.g., Walnut, Left, Heavy Duty')
    sequence = fields.Integer(string='Sequence', default=10)
    bom_category_id = fields.Many2one(related='variable_id.bom_category_id')
    product_id = fields.Many2one('product.product', string='Linked Product',
                                 domain="[('product_tmpl_id.bom_category_id', 'child_of', bom_category_id)]",
                                 help='Inventory product for product-type variables')
    surcharge_type = fields.Selection([
        ('none', 'No Surcharge'),
        ('per_unit', 'Per Computed Unit (m\u00b2/m\u00b3/m)'),
        ('fixed', 'Fixed Per Piece'),
    ], string='Surcharge Type', default='none')
    surcharge_amount = fields.Float(string='Surcharge Amount', digits='Product Price')
    qty_override = fields.Float(string='Qty Override',
                                help='Override BOM component quantity. 0 = keep default.')
    is_default = fields.Boolean(string='Default')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id and not self.name:
            self.name = self.product_id.name
