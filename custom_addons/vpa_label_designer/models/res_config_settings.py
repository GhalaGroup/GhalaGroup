# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    label_default_dpi = fields.Selection([
        ('203', '203 DPI'),
        ('300', '300 DPI'),
        ('600', '600 DPI'),
    ], string='Default DPI',
        config_parameter='vpa_label_designer.default_dpi',
        default='203')

    label_default_printer_id = fields.Many2one(
        'vpa.printer.config', string='Default Printer',
        config_parameter='vpa_label_designer.default_printer_id')

    label_preview_api = fields.Selection([
        ('labelary', 'Labelary API (api.labelary.com)'),
        ('none', 'No Preview'),
    ], string='Preview Method',
        config_parameter='vpa_label_designer.preview_api',
        default='labelary')

    # Statistics
    total_templates = fields.Integer(
        string='Label Templates',
        compute='_compute_label_statistics')
    total_printers = fields.Integer(
        string='Configured Printers',
        compute='_compute_label_statistics')
    total_label_sizes = fields.Integer(
        string='Label Sizes',
        compute='_compute_label_statistics')

    @api.depends_context('company')
    def _compute_label_statistics(self):
        for record in self:
            company = record.company_id or self.env.company
            record.total_templates = self.env['vpa.label.template'].search_count([
                ('company_id', 'in', [False, company.id]),
            ])
            record.total_printers = self.env['vpa.printer.config'].search_count([
                ('company_id', 'in', [False, company.id]),
            ])
            record.total_label_sizes = self.env['vpa.label.size'].search_count([
                ('company_id', 'in', [False, company.id]),
            ])
