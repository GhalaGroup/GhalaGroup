# -*- coding: utf-8 -*-
from odoo import fields, models


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    scales_with_dimensions = fields.Boolean(
        string='Scales with Dimensions',
        help='If checked, this component quantity will be multiplied by the computed '
             'area/volume from the product configurator.',
    )
    linked_variable_id = fields.Many2one(
        'vpa.config.variable',
        string='Linked Config Variable',
        help='Link this BOM component to a configuration variable. '
             'The placeholder product will be replaced by the user\'s selection during manufacturing.',
    )
    dimension_qty_formula = fields.Text(
        string='Custom Qty Formula',
        help='Optional Python expression for custom quantity calculation. '
             'Available variables: same as dimension template formulas plus computed_qty.',
    )
