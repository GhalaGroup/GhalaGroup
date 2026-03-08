# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CommissionYearSummaryWizard(models.TransientModel):
    _name = 'vpa.commission.year.summary.wizard'
    _description = 'Commission Year Summary Report Wizard'

    @api.model
    def _get_year_selection(self):
        current_year = fields.Date.today().year
        return [(str(y), str(y)) for y in range(2020, current_year + 3)]

    year = fields.Selection(
        selection='_get_year_selection',
        string='Year',
        required=True,
        default=lambda self: str(fields.Date.today().year),
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )

    def get_year_lines(self):
        """Return all scheme year records for the selected year."""
        self.ensure_one()
        return self.env['vpa.commission.scheme.year'].search([
            ('year', '=', self.year),
            ('company_id', '=', self.company_id.id),
        ], order='employee_id')

    def action_print(self):
        self.ensure_one()
        if not self.get_year_lines():
            raise UserError(_('No commission scheme years found for %s.', self.year))
        return self.env.ref(
            'vpa_sales_commission.action_report_commission_year_summary'
        ).report_action(self, config={'report_type': 'qweb-html'})
