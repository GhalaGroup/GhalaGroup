# -*- coding: utf-8 -*-
# Part of VPA Login Theme. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Add a button/link to open Login Theme configuration
    def action_open_login_theme(self):
        """Open Login Theme configuration"""
        self.env['login.theme.config'].check_access('read')

        # Get or create theme config for current company
        theme = self.env['login.theme.config'].search([
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if not theme:
            # Create default theme if none exists
            theme = self.env['login.theme.config'].create({
                'theme_name': f'{self.env.company.name} Login Theme',
                'company_id': self.env.company.id,
                'preset_theme': 'red',
            })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Login Theme Configuration',
            'res_model': 'login.theme.config',
            'res_id': theme.id,
            'view_mode': 'form',
            'target': 'current',
        }
