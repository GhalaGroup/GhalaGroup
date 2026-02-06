# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from datetime import datetime


class ChangeEffectiveWizardMO(models.TransientModel):
    _name = "change.effective.wizard.mo"
    _description = "Change Effective Date - Manufacturing Order"

    production_id = fields.Many2one('mrp.production', string="Manufacturing Order", readonly=True)
    original_date = fields.Datetime(string="Original Completion Date", readonly=True)
    effective_date = fields.Datetime(string="New Effective Date", required=True,
                                     help="Date at which the Manufacturing Order was completed")

    @api.model
    def default_get(self, fields_list):
        res = super(ChangeEffectiveWizardMO, self).default_get(fields_list)
        if self._context.get('active_id'):
            production = self.env['mrp.production'].browse(self._context.get('active_id'))
            res['production_id'] = production.id
            res['original_date'] = production.date_finished
            res['effective_date'] = production.date_finished
        return res

    def update_effective_date(self):
        """Update the effective date for the Manufacturing Order and all related records."""
        self.ensure_one()

        if not self.production_id:
            return

        production = self.production_id
        selected_date = self.effective_date

        # Use the model's _apply_effective_date method
        production._apply_effective_date(selected_date)

        return {'type': 'ir.actions.act_window_close'}
