# -*- coding: utf-8 -*-
from odoo import api, fields, models


class VpaDisplayGroup(models.Model):
    _name = 'vpa.display.group'
    _description = 'Display Group'
    _order = 'sequence, id'

    template_id = fields.Many2one('vpa.dimension.template', string='Template',
                                  required=True, ondelete='cascade')
    name = fields.Char(string='Group Name', required=True, help='e.g., Door Leaf, Frame, Hardware')
    code = fields.Char(string='Code', help='Short code (e.g., leaf, frame, hardware)')
    sequence = fields.Integer(string='Sequence', default=10)
    show_dimensions = fields.Boolean(string='Show Dimensions',
                                     help='Whether this group displays the main dimensions (e.g., Size group)')
    note_format = fields.Text(
        string='Note Format',
        help='Template for quotation note line. Use {field_code} placeholders.\n'
             'Example: "Frame: {w}×{h}mm, Depth {frame_depth}mm"',
    )
    extra_dimension_ids = fields.Many2many(
        'vpa.dimension.template.line',
        'vpa_display_group_dimension_rel',
        'group_id', 'dimension_id',
        string='Extra Dimensions',
        help='Additional dimensions shown in this group only (e.g., Frame Depth in Frame group)',
    )
    variable_ids = fields.One2many('vpa.config.variable', 'display_group_id', string='Variables')

    @api.onchange('name')
    def _onchange_name(self):
        if self.name and not self.code:
            self.code = self.name.strip().lower().replace(' ', '_')
