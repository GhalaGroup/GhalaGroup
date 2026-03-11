# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools

QUARTER_SELECTION = [
    ('Q1', 'Q1 (Jan–Mar)'),
    ('Q2', 'Q2 (Apr–Jun)'),
    ('Q3', 'Q3 (Jul–Sep)'),
    ('Q4', 'Q4 (Oct–Dec)'),
]

MONTH_SELECTION = [
    ('01', 'January'), ('02', 'February'), ('03', 'March'),
    ('04', 'April'), ('05', 'May'), ('06', 'June'),
    ('07', 'July'), ('08', 'August'), ('09', 'September'),
    ('10', 'October'), ('11', 'November'), ('12', 'December'),
]


class SoCommissionReport(models.Model):
    _name = 'so.commission.report'
    _description = 'Commission by Sales Order'
    _auto = False
    _order = 'sale_order_name asc'

    # Sales Order info
    sale_order_name = fields.Char(string='Sales Order', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Client', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)

    # Date fields for filtering/grouping
    date_year = fields.Char(string='Year', readonly=True)
    date_quarter = fields.Selection(QUARTER_SELECTION, string='Quarter', readonly=True)
    date_month = fields.Selection(MONTH_SELECTION, string='Month', readonly=True)
    date = fields.Date(string='Date', readonly=True)

    # Counts
    mo_count = fields.Integer(string='# MOs', readonly=True)
    line_count = fields.Integer(string='# Lines', readonly=True)

    # Financials
    rate = fields.Float(string='Rate (%)', readonly=True, digits=(5, 2))
    total_amount = fields.Float(string='Commission Amount', readonly=True, digits=(12, 2))
    paid_amount = fields.Float(string='Paid', readonly=True, digits=(12, 2))
    outstanding_amount = fields.Float(string='Outstanding', readonly=True, digits=(12, 2))
    base_amount = fields.Float(string='Base Amount', readonly=True, digits=(12, 2))

    # Status summary
    pending_amount = fields.Float(string='Pending', readonly=True, digits=(12, 2))
    confirmed_amount = fields.Float(string='Confirmed', readonly=True, digits=(12, 2))

    def action_print_pdf(self):
        """Print PDF for all currently displayed records (respects active filters)."""
        records = self if self else self.search([])
        years = sorted(set(r.date_year for r in records if r.date_year))
        employees = sorted(set(r.employee_id.name for r in records if r.employee_id))
        parts = []
        if years:
            parts.append(', '.join(years))
        if employees:
            parts.append(', '.join(employees))
        subtitle = ' \u2014 '.join(parts) if parts else ''
        return self.env.ref(
            'vpa_sales_commission.action_report_so_commission_report'
        ).report_action(records, data={'subtitle': subtitle, 'ids': records.ids, 'model': 'so.commission.report'})

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY
                        COALESCE(cl.sale_order_name, 'No SO'),
                        cl.employee_id,
                        rc.id
                    ) AS id,
                    COALESCE(cl.sale_order_name, 'No SO') AS sale_order_name,
                    COALESCE(so_via_line.partner_id, so_via_origin.partner_id) AS partner_id,
                    cl.employee_id AS employee_id,
                    rc.id AS company_id,
                    rc.currency_id AS currency_id,
                    MAX(cl.date_year) AS date_year,
                    CASE EXTRACT(QUARTER FROM MAX(cl.date))
                        WHEN 1 THEN 'Q1'
                        WHEN 2 THEN 'Q2'
                        WHEN 3 THEN 'Q3'
                        WHEN 4 THEN 'Q4'
                    END AS date_quarter,
                    TO_CHAR(MAX(cl.date), 'MM') AS date_month,
                    MAX(cl.date) AS date,
                    COUNT(DISTINCT cl.production_id) AS mo_count,
                    COUNT(cl.id) AS line_count,
                    AVG(cl.rate) AS rate,
                    SUM(cl.amount) AS total_amount,
                    SUM(cl.amount_paid) AS paid_amount,
                    GREATEST(0.0, SUM(cl.amount) - SUM(cl.amount_paid)) AS outstanding_amount,
                    SUM(cl.base_amount) AS base_amount,
                    SUM(CASE WHEN cl.state = 'pending' THEN cl.amount ELSE 0 END) AS pending_amount,
                    SUM(CASE WHEN cl.state IN ('confirmed', 'paid') THEN cl.amount ELSE 0 END) AS confirmed_amount
                FROM vpa_commission_line cl
                JOIN vpa_commission_scheme cs ON cs.id = cl.scheme_id
                JOIN res_company rc ON rc.id = cs.company_id
                LEFT JOIN mrp_production mp ON mp.id = cl.production_id
                LEFT JOIN sale_order_line sol ON sol.id = mp.sale_line_id
                LEFT JOIN sale_order so_via_line ON so_via_line.id = sol.order_id
                LEFT JOIN sale_order so_via_origin ON so_via_origin.name = mp.origin
                WHERE cl.state != 'cancelled'
                GROUP BY
                    COALESCE(cl.sale_order_name, 'No SO'),
                    COALESCE(so_via_line.partner_id, so_via_origin.partner_id),
                    cl.employee_id,
                    rc.id,
                    rc.currency_id
            )
        """ % self._table
        self.env.cr.execute(query)
