# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    nns_show_override = fields.Boolean(
        string='Show Negative-Stock Override',
        compute='_compute_nns_show_override',
        help='Technical: whether to show the negative-stock override button.',
    )

    @api.depends('state', 'company_id')
    def _compute_nns_show_override(self):
        can_override = self.env.user.has_group(
            'vpa_no_negative_stock.group_stock_sentinel_override')
        for picking in self:
            company = picking.company_id or self.env.company
            # Only relevant in Soft Warn mode: that is the only mode where an
            # override applies. In Hard Block there is no override, so no button.
            picking.nns_show_override = bool(
                can_override
                and company.nns_enabled
                and company.nns_mode == 'warn'
                and picking.state not in ('draft', 'done', 'cancel'))

    def button_validate(self):
        # Tag the document reference so Stock Sentinel logs capture it.
        self = self.with_context(
            nns_document_ref=self.display_name if len(self) == 1 else None)
        return super().button_validate()

    def action_nns_override(self):
        """Open the manager override wizard for this picking."""
        self.ensure_one()
        return {
            'name': 'Override Negative Stock',
            'type': 'ir.actions.act_window',
            'res_model': 'nns.override.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': 'stock.picking',
                'active_id': self.id,
            },
        }
