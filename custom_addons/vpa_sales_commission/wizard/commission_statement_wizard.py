# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CommissionStatementWizard(models.TransientModel):
    _name = 'vpa.commission.statement.wizard'
    _description = 'Commission Statement Wizard'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
    )
    date_from = fields.Date(
        string='Date From',
        required=True,
    )
    date_to = fields.Date(
        string='Date To',
        required=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        compute='_compute_currency',
    )
    include_pending = fields.Boolean(
        string='Include Pending Lines',
        default=True,
    )

    @api.depends('employee_id')
    def _compute_currency(self):
        for wizard in self:
            if wizard.employee_id:
                scheme = self.env['vpa.commission.scheme'].search([
                    ('employee_id', '=', wizard.employee_id.id),
                ], limit=1)
                wizard.currency_id = scheme.currency_id if scheme else self.env.company.currency_id
            else:
                wizard.currency_id = self.env.company.currency_id

    def get_period_label(self):
        """Return formatted period label for the report."""
        self.ensure_one()
        return '%s - %s' % (
            self.date_from.strftime('%d/%m/%Y'),
            self.date_to.strftime('%d/%m/%Y'),
        )

    def get_commission_lines(self):
        """Return commission lines for the employee within the date range."""
        self.ensure_one()
        domain = [
            ('employee_id', '=', self.employee_id.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', '!=', 'cancelled'),
        ]
        if not self.include_pending:
            domain.append(('state', 'in', ('confirmed', 'paid')))
        return self.env['vpa.commission.line'].search(domain, order='date asc')

    def get_totals(self, lines):
        """Compute totals from commission lines."""
        self.ensure_one()
        total_earned = sum(lines.mapped('amount'))
        total_confirmed = sum(lines.filtered(lambda l: l.state in ('confirmed', 'paid')).mapped('amount'))
        total_pending = sum(lines.filtered(lambda l: l.state == 'pending').mapped('amount'))
        total_paid = sum(lines.filtered(lambda l: l.state == 'paid').mapped('amount'))
        return {
            'total_earned': total_earned,
            'total_confirmed': total_confirmed,
            'total_pending': total_pending,
            'total_paid': total_paid,
            'outstanding': max(0.0, total_earned - total_paid),
        }

    def action_print_statement(self):
        """Generate the PDF commission statement."""
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_('Date From must be before Date To.'))
        lines = self.get_commission_lines()
        if not lines:
            raise UserError(_('No commission lines found for %s in the selected period.', self.employee_id.name))
        return self.env.ref(
            'vpa_sales_commission.action_report_commission_statement_wizard'
        ).report_action(self)
