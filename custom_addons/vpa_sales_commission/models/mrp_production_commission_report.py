# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class MrpProductionCommissionReport(models.Model):
    _name = 'mrp.production.commission.report'
    _description = 'MO Commission Report'
    _auto = False
    _order = 'date_finished desc, id desc'

    # MO Information
    production_id = fields.Many2one('mrp.production', string='Manufacturing Order', readonly=True)
    name = fields.Char(string='MO Reference', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_qty = fields.Float(string='Quantity', readonly=True, digits=(12, 2))
    date_finished = fields.Datetime(string='Date Finished', readonly=True)
    date_year = fields.Char(string='Year', readonly=True)
    date_month = fields.Char(string='Month', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('progress', 'In Progress'),
        ('to_close', 'To Close'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True)

    # Commission Status
    commission_blocked = fields.Boolean(string='Commission Blocked', readonly=True)
    commission_generated = fields.Boolean(string='Has Commission', readonly=True)
    commission_status = fields.Selection([
        ('not_applicable', 'Not Applicable'),
        ('pending_generation', 'Pending Generation'),
        ('pending_approval', 'Pending Approval'),
        ('applied', 'Approved'),
        ('paid', 'Paid'),
    ], string='Commission Status', readonly=True)

    # Financial Information
    commission_base_amount = fields.Float(string='Base Amount', readonly=True, digits=(12, 2))
    total_commission_amount = fields.Float(string='Total Commission', readonly=True, digits=(12, 2))
    commission_per_item = fields.Float(
        string='Commission Per Item', readonly=True, digits=(12, 2),
        aggregator='avg',
        help='Total commission divided by the quantity produced — the '
             'commission carried by each unit of the finished item.',
    )
    pending_commission_amount = fields.Float(string='Pending Commission', readonly=True, digits=(12, 2))
    confirmed_commission_amount = fields.Float(string='Confirmed Commission', readonly=True, digits=(12, 2))
    paid_commission_amount = fields.Float(string='Paid Commission', readonly=True, digits=(12, 2))

    # Counts
    commission_line_count = fields.Integer(string='# of Commission Lines', readonly=True)
    employee_count = fields.Integer(string='# of Employees', readonly=True)

    # Billing status
    billed_line_count = fields.Integer(string='Billed Lines', readonly=True)
    billing_status = fields.Selection([
        ('not_billed', 'Not Billed'),
        ('partial', 'Partially Billed'),
        ('billed', 'Billed'),
    ], string='Billing Status', readonly=True)

    # Company
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    mp.id AS id,
                    mp.id AS production_id,
                    mp.name AS name,
                    mp.product_id AS product_id,
                    mp.product_qty AS product_qty,
                    mp.date_finished AS date_finished,
                    EXTRACT(YEAR FROM mp.date_finished)::text AS date_year,
                    TO_CHAR(mp.date_finished, 'YYYY-MM') AS date_month,
                    mp.state AS state,
                    mp.commission_blocked AS commission_blocked,
                    CASE
                        WHEN COUNT(cl.id) > 0 THEN true
                        ELSE false
                    END AS commission_generated,

                    -- Commission Status Logic — a work queue, in order:
                    --   pending_generation: no commission lines yet
                    --   pending_approval:   at least one line awaits approval
                    --   paid:               every line settled ('paid' state,
                    --                       or amount_due ~0 via the year's
                    --                       proportional cash settlement)
                    --   applied (Approved): approved, waiting for payment
                    CASE
                        WHEN mp.commission_blocked = true THEN 'not_applicable'
                        WHEN COUNT(cl.id) = 0 THEN 'pending_generation'
                        WHEN COUNT(cl.id) FILTER (WHERE cl.state = 'pending') > 0 THEN 'pending_approval'
                        WHEN COUNT(cl.id) FILTER (WHERE cl.state = 'paid' OR cl.amount_due <= 0.01) = COUNT(cl.id) THEN 'paid'
                        ELSE 'applied'
                    END AS commission_status,

                    COALESCE(MAX(cl.base_amount), 0) AS commission_base_amount,
                    COALESCE(SUM(cl.amount), 0) AS total_commission_amount,
                    -- Commission carried by each unit produced. Guarded against
                    -- MOs with no quantity so the view never divides by zero.
                    CASE
                        WHEN mp.product_qty > 0
                        THEN COALESCE(SUM(cl.amount), 0) / mp.product_qty
                        ELSE 0
                    END AS commission_per_item,
                    COALESCE(SUM(CASE WHEN cl.state = 'pending' THEN cl.amount ELSE 0 END), 0) AS pending_commission_amount,
                    COALESCE(SUM(CASE WHEN cl.state = 'confirmed' THEN cl.amount ELSE 0 END), 0) AS confirmed_commission_amount,
                    COALESCE(SUM(CASE WHEN cl.state = 'paid' THEN cl.amount ELSE 0 END), 0) AS paid_commission_amount,
                    COUNT(cl.id) AS commission_line_count,
                    COUNT(DISTINCT cl.employee_id) AS employee_count,

                    -- Billing Status
                    COUNT(cl.id) FILTER (WHERE cl.bill_id IS NOT NULL) AS billed_line_count,
                    CASE
                        WHEN COUNT(cl.id) = 0 THEN 'not_billed'
                        WHEN COUNT(cl.id) FILTER (WHERE cl.bill_id IS NOT NULL) = COUNT(cl.id) THEN 'billed'
                        WHEN COUNT(cl.id) FILTER (WHERE cl.bill_id IS NOT NULL) > 0 THEN 'partial'
                        ELSE 'not_billed'
                    END AS billing_status,

                    mp.company_id AS company_id,
                    rc.currency_id AS currency_id

                FROM mrp_production mp
                LEFT JOIN vpa_commission_line cl ON cl.production_id = mp.id AND cl.state != 'cancelled'
                LEFT JOIN res_company rc ON rc.id = mp.company_id
                WHERE mp.state IN ('to_close', 'done')
                GROUP BY mp.id, mp.name, mp.product_id, mp.product_qty, mp.date_finished,
                         mp.state, mp.commission_blocked,
                         mp.company_id, rc.currency_id
            )
        """ % self._table
        self.env.cr.execute(query)

    def action_open_production(self):
        """Open the manufacturing order form."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': self.production_id.id,
            'target': 'current',
        }

    def action_view_commission_lines(self):
        """View commission lines for this MO."""
        self.ensure_one()
        return {
            'name': 'Commission Lines',
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.commission.line',
            'view_mode': 'list,form',
            'domain': [('production_id', '=', self.production_id.id)],
            'context': {'default_production_id': self.production_id.id},
        }

    def action_generate_commission(self):
        """Generate commission for this MO."""
        self.ensure_one()
        return self.production_id.action_generate_commission()

    def action_mark_not_applicable(self):
        """Mark selected MOs as Not Applicable (block commission)."""
        productions = self.mapped('production_id').filtered(lambda p: not p.commission_blocked)
        productions.write({'commission_blocked': True})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Done',
                'message': '%d MO(s) marked as Not Applicable.' % len(productions),
                'type': 'success',
                'sticky': False,
                # refresh the list so the new status shows immediately
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
            },
        }

    def action_remove_not_applicable(self):
        """Remove Not Applicable from selected MOs."""
        productions = self.mapped('production_id').filtered(lambda p: p.commission_blocked)
        productions.write({'commission_blocked': False})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Done',
                'message': '%d MO(s) re-enabled for commission.' % len(productions),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
            },
        }
