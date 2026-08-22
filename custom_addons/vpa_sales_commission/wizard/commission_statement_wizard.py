# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


MONTH_SELECTION = [
    ('', 'All Months'),
    ('1', 'January'), ('2', 'February'), ('3', 'March'),
    ('4', 'April'), ('5', 'May'), ('6', 'June'),
    ('7', 'July'), ('8', 'August'), ('9', 'September'),
    ('10', 'October'), ('11', 'November'), ('12', 'December'),
]


class CommissionStatementWizard(models.TransientModel):
    _name = 'vpa.commission.statement.wizard'
    _description = 'Commission Statement Wizard'

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        domain="[('commission_scheme_ids.company_id', '=', company_id)]",
        help='Only employees with a commission scheme in the selected '
             'company — a statement is meaningless for anyone else.',
    )

    @api.model
    def _get_year_selection(self):
        current_year = fields.Date.today().year
        return [(str(y), str(y)) for y in range(2020, current_year + 2)]

    year = fields.Selection(
        selection='_get_year_selection',
        string='Year',
        required=True,
        default=lambda self: str(fields.Date.today().year),
    )
    month = fields.Selection(
        selection=MONTH_SELECTION,
        string='Month',
        default='',
    )

    # computed date range (used by get_commission_lines and report)
    date_from = fields.Date(compute='_compute_dates', store=False)
    date_to = fields.Date(compute='_compute_dates', store=False)

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        compute='_compute_currency',
    )
    include_pending = fields.Boolean(
        string='Include Pending Lines',
        default=True,
    )

    @api.depends('year', 'month')
    def _compute_dates(self):
        for wizard in self:
            if not wizard.year:
                wizard.date_from = False
                wizard.date_to = False
                continue
            y = int(wizard.year)
            if wizard.month:
                m = int(wizard.month)
                wizard.date_from = fields.Date.from_string('%04d-%02d-01' % (y, m))
                wizard.date_to = wizard.date_from + relativedelta(months=1, days=-1)
            else:
                wizard.date_from = fields.Date.from_string('%04d-01-01' % y)
                wizard.date_to = fields.Date.from_string('%04d-12-31' % y)

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
        if self.month:
            month_name = dict(MONTH_SELECTION).get(self.month, '')
            return '%s %s' % (month_name, self.year)
        return 'FY %s' % self.year

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
        """Compute totals from commission lines.

        Paid uses the lines' PROPORTIONAL settlement (amount_paid), not the
        line state: cash moves at year level, and line state only flips to
        'paid' when a year closes — state-based totals showed Paid 0.00 on
        fully-paid open years."""
        self.ensure_one()
        total_earned = sum(lines.mapped('amount'))
        total_confirmed = sum(lines.filtered(lambda l: l.state in ('confirmed', 'paid')).mapped('amount'))
        total_pending = sum(lines.filtered(lambda l: l.state == 'pending').mapped('amount'))
        total_paid = sum(lines.mapped('amount_paid'))
        return {
            'total_earned': total_earned,
            'total_confirmed': total_confirmed,
            'total_pending': total_pending,
            'total_paid': total_paid,
            'outstanding': max(0.0, total_earned - total_paid),
        }

    def get_year_settlements(self):
        """The scheme-year settlement records behind this statement — the
        same cash figures the Commission Centre card shows (guarantee, total
        to pay, cash paid, write-offs, still to pay). Printed alongside the
        earned-commission detail so the employee gets the FULL picture:
        performance AND money actually received."""
        self.ensure_one()
        return self.env['vpa.commission.scheme.year'].search([
            ('employee_id', '=', self.employee_id.id),
            ('company_id', '=', self.company_id.id),
            ('year', '=', self.year),
        ])

    def get_so_lines(self, lines):
        """Group commission lines by Sales Order for SO-consolidated report."""
        so_groups = {}
        for line in lines:
            so_key = line.sale_order_name or 'No SO'
            if so_key not in so_groups:
                partner_name = False
                customer_ref = False
                if line.production_id and line.production_id.sale_line_id:
                    order = line.production_id.sale_line_id.order_id
                    partner_name = order.partner_id.name
                    customer_ref = order.client_order_ref
                so_groups[so_key] = {
                    'so_name': so_key,
                    'client_name': partner_name or '\u2014',
                    'customer_ref': customer_ref or '\u2014',
                    'mo_count': 0,
                    'total_amount': 0.0,
                    'total_paid': 0.0,
                    'rate_sum': 0.0,
                }
            so_groups[so_key]['mo_count'] += 1
            so_groups[so_key]['total_amount'] += line.amount
            so_groups[so_key]['total_paid'] += line.amount_paid
            so_groups[so_key]['rate_sum'] += line.rate
        result = []
        for grp in so_groups.values():
            grp['rate'] = grp['rate_sum'] / grp['mo_count'] if grp['mo_count'] else 0.0
            grp['outstanding'] = max(0.0, grp['total_amount'] - grp['total_paid'])
            result.append(grp)
        result.sort(key=lambda x: x['so_name'])
        return result

    def action_print_by_so(self):
        """Preview the SO-consolidated commission statement in browser."""
        self.ensure_one()
        lines = self.get_commission_lines()
        if not lines:
            raise UserError(_('No commission lines found for %s in the selected period.', self.employee_id.name))
        action = self.env.ref(
            'vpa_sales_commission.action_report_commission_statement_by_so'
        ).report_action(self)
        action['report_type'] = 'qweb-html'
        return action

    def action_pdf_by_so(self):
        """Download PDF of the SO-consolidated commission statement."""
        self.ensure_one()
        lines = self.get_commission_lines()
        if not lines:
            raise UserError(_('No commission lines found for %s in the selected period.', self.employee_id.name))
        return self.env.ref(
            'vpa_sales_commission.action_report_commission_statement_by_so'
        ).report_action(self)

    def action_print_statement(self):
        """Preview the commission statement in browser."""
        self.ensure_one()
        lines = self.get_commission_lines()
        if not lines:
            raise UserError(_('No commission lines found for %s in the selected period.', self.employee_id.name))
        action = self.env.ref(
            'vpa_sales_commission.action_report_commission_statement_wizard'
        ).report_action(self)
        action['report_type'] = 'qweb-html'
        return action

    def action_pdf_statement(self):
        """Download PDF of the commission statement."""
        self.ensure_one()
        lines = self.get_commission_lines()
        if not lines:
            raise UserError(_('No commission lines found for %s in the selected period.', self.employee_id.name))
        return self.env.ref(
            'vpa_sales_commission.action_report_commission_statement_wizard'
        ).report_action(self)
