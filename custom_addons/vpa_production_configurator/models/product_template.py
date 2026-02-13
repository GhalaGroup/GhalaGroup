# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    dimension_template_id = fields.Many2one('vpa.dimension.template', string='Dimension Template',
                                            help='Assign a dimension template for configurator-based pricing')
    has_dimensions = fields.Boolean(string='Has Dimensions', compute='_compute_has_dimensions', store=True)
    dimension_rate = fields.Float(string='Dimension Rate', digits='Product Price',
                                  related='dimension_template_id.default_rate', readonly=True,
                                  help='Rate per computed unit (m\u00b2/m\u00b3/m) from the dimension template.')

    @api.depends('dimension_template_id')
    def _compute_has_dimensions(self):
        for rec in self:
            rec.has_dimensions = bool(rec.dimension_template_id)

    def _get_dimension_rate(self):
        """Get the rate from the dimension template."""
        self.ensure_one()
        if self.dimension_template_id:
            return self.dimension_template_id.default_rate
        return 0.0
