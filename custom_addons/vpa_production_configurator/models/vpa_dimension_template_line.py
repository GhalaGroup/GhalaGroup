# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class VpaDimensionTemplateLine(models.Model):
    _name = 'vpa.dimension.template.line'
    _description = 'Dimension Template Line'
    _order = 'sequence, id'

    template_id = fields.Many2one('vpa.dimension.template', string='Template',
                                  required=True, ondelete='cascade')
    name = fields.Char(string='Label', required=True, help='e.g., Width, Height, Depth')
    field_code = fields.Char(string='Code', required=True,
                             help='Short code used in formulas (e.g., w, h, d)')
    uom_type = fields.Selection([
        ('mm', 'Millimeters (mm)'),
        ('cm', 'Centimeters (cm)'),
        ('m', 'Meters (m)'),
    ], string='Unit', required=True, default='mm')
    sequence = fields.Integer(string='Sequence', default=10)
    default_value = fields.Float(string='Default Value')
    min_value = fields.Float(string='Minimum')
    max_value = fields.Float(string='Maximum', help='0 = no maximum')
    required = fields.Boolean(string='Required', default=True)
    show_on_quotation = fields.Boolean(string='Show on Quotation', default=True,
                                       help='Whether to display this dimension on the customer quotation')

    @api.constrains('field_code')
    def _check_field_code(self):
        for rec in self:
            if rec.field_code and not rec.field_code.isidentifier():
                raise ValidationError(
                    _("Code '%s' is not a valid Python identifier. Use only letters, numbers, and underscores.", rec.field_code)
                )
            # Check uniqueness within template
            duplicates = self.search([
                ('template_id', '=', rec.template_id.id),
                ('field_code', '=', rec.field_code),
                ('id', '!=', rec.id),
            ])
            if duplicates:
                raise ValidationError(
                    _("Code '%s' is already used in this template.", rec.field_code)
                )
