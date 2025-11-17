# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    vpa_layout_selected = fields.Boolean(
        string='VPA Layout Selected',
        compute='_compute_vpa_layout_selected'
    )

    @api.depends('company_id.external_report_layout_id')
    def _compute_vpa_layout_selected(self):
        """Check if VPA Document Layout is selected for the company"""
        for record in self:
            vpa_layout = self.env.ref('vpa_document_layout.report_layout_vpa', raise_if_not_found=False)
            record.vpa_layout_selected = (
                vpa_layout and
                record.company_id.external_report_layout_id == vpa_layout
            )

    def action_open_vpa_config(self):
        """Open VPA Document Configuration for the current company"""
        self.ensure_one()

        # Get or create VPA config for this company
        vpa_config = self.env['vpa.document.config'].search([
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not vpa_config:
            vpa_config = self.env['vpa.document.config'].create({
                'company_id': self.company_id.id,
                'name': f'VPA Layout Config - {self.company_id.name}'
            })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit VPA Document Layout',
            'res_model': 'vpa.document.config',
            'res_id': vpa_config.id,
            'view_mode': 'form',
            'target': 'current',
        }
