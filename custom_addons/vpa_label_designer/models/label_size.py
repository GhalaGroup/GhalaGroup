# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class LabelSize(models.Model):
    _name = 'vpa.label.size'
    _description = 'Label Paper Size'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    width_mm = fields.Float(string='Width (mm)', required=True, digits=(10, 2))
    height_mm = fields.Float(string='Height (mm)', required=True, digits=(10, 2))
    dpi = fields.Selection([
        ('203', '203 DPI'),
        ('300', '300 DPI'),
        ('600', '600 DPI'),
    ], string='Printer DPI', required=True, default='203')

    width_dots = fields.Integer(string='Width (dots)', compute='_compute_dots', store=True)
    height_dots = fields.Integer(string='Height (dots)', compute='_compute_dots', store=True)

    has_rfid = fields.Boolean(string='RFID Capable', default=False)
    rfid_position = fields.Selection([
        ('center', 'Center'),
        ('bottom', 'Bottom'),
        ('top', 'Top'),
        ('left', 'Left'),
        ('right', 'Right'),
    ], string='RFID Inlay Position', default='center')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    _positive_width = models.Constraint('CHECK(width_mm > 0)', 'Width must be positive.')
    _positive_height = models.Constraint('CHECK(height_mm > 0)', 'Height must be positive.')

    @api.depends('width_mm', 'height_mm', 'dpi')
    def _compute_dots(self):
        for rec in self:
            dpi_val = int(rec.dpi) if rec.dpi else 203
            rec.width_dots = int(rec.width_mm * (dpi_val / 25.4))
            rec.height_dots = int(rec.height_mm * (dpi_val / 25.4))

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.name} ({rec.width_mm}x{rec.height_mm}mm, {rec.dpi} DPI)"
            result.append((rec.id, name))
        return result
