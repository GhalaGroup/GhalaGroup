# -*- coding: utf-8 -*-
from odoo import models


class ResCompany(models.Model):
    _inherit = 'res.company'

    def unlink(self):
        """Override unlink to allow company deletion by auto-deleting VPA configs"""
        # Find and delete associated VPA configs first
        vpa_configs = self.env['vpa.document.config'].search([('company_id', 'in', self.ids)])
        if vpa_configs:
            vpa_configs.unlink()

        return super().unlink()

    def action_open_vpa_config(self):
        """Open VPA Document Configuration for this company"""
        self.ensure_one()

        # Get or create VPA config for this company
        vpa_config = self.env['vpa.document.config'].search([
            ('company_id', '=', self.id)
        ], limit=1)

        if not vpa_config:
            vpa_config = self.env['vpa.document.config'].create({
                'company_id': self.id,
                'name': f'VPA Layout Config - {self.name}'
            })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit VPA Document Layout',
            'res_model': 'vpa.document.config',
            'res_id': vpa_config.id,
            'view_mode': 'form',
            'target': 'current',
        }
