# -*- coding: utf-8 -*-
from odoo import fields, models


class VpaConfigVariable(models.Model):
    _name = 'vpa.config.variable'
    _description = 'Configuration Variable'
    _order = 'sequence, id'

    template_id = fields.Many2one('vpa.dimension.template', string='Template',
                                  required=True, ondelete='cascade')
    display_group_id = fields.Many2one('vpa.display.group', string='Display Group',
                                       domain="[('template_id', '=', template_id)]",
                                       help='Which display group this variable belongs to')
    name = fields.Char(string='Variable Name', required=True, help='e.g., Veneer Type, Door Opening')
    sequence = fields.Integer(string='Sequence', default=10)
    variable_type = fields.Selection([
        ('simple', 'Simple Selection'),
        ('product', 'Product Selection'),
    ], string='Type', required=True, default='simple',
        help='Simple: text options. Product: linked to inventory products.')
    bom_category_id = fields.Many2one('vpa.bom.category', string='BOM Category',
                                      help='Filter product options to this BOM category')
    affects_price = fields.Boolean(string='Affects Price',
                                   help='Whether selections from this variable change the price')
    required = fields.Boolean(string='Required', default=True)
    option_ids = fields.One2many('vpa.config.variable.option', 'variable_id', string='Options', copy=True)
