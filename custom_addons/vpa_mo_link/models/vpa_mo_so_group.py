# -*- coding: utf-8 -*-
from odoo import models, fields, tools, _


class VpaMoSoGroup(models.Model):
    """
    Read-only card per Sales Order that has Manufacturing Orders,
    plus one 'Other Orders' card for MOs not linked to any Sales Order.
    Backed by a SQL view over mrp_production grouped by vpa_so_group.
    """
    _name = 'vpa.mo.so.group'
    _description = 'Manufacturing Orders by Sales Order'
    _auto = False
    _order = 'sort_key, name'

    name = fields.Char(string='Sales Order', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    sale_id = fields.Many2one('sale.order', string='Sales Order Ref', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    client_order_ref = fields.Char(string='Customer Reference', readonly=True)
    user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)
    amount_total = fields.Monetary(string='Order Total', currency_field='currency_id', readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)
    commitment_date = fields.Date(string='Delivery Date', readonly=True)
    next_date_start = fields.Date(string='Planned Start', readonly=True)
    start_overdue = fields.Boolean(string='Start Overdue', readonly=True)
    oldest_mo_date = fields.Date(string='Oldest MO Created', readonly=True)
    newest_mo_date = fields.Date(string='Newest MO Created', readonly=True)
    qty_total = fields.Float(string='Total Quantity', readonly=True)
    mo_count = fields.Integer(string='Manufacturing Orders', readonly=True)
    mo_todo_count = fields.Integer(string='In Progress', readonly=True)
    mo_done_count = fields.Integer(string='Done', readonly=True)
    progress = fields.Integer(string='Progress %', readonly=True)
    sort_key = fields.Integer(readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW vpa_mo_so_group AS (
                SELECT
                    MIN(mp.id) AS id,
                    mp.vpa_so_group AS name,
                    mp.company_id AS company_id,
                    MIN(so.id) AS sale_id,
                    MIN(so.partner_id) AS partner_id,
                    MIN(so.client_order_ref) AS client_order_ref,
                    MIN(so.user_id) AS user_id,
                    MIN(so.amount_total) AS amount_total,
                    MIN(so.currency_id) AS currency_id,
                    MIN(so.commitment_date)::date AS commitment_date,
                    (MIN(mp.date_start) FILTER (WHERE mp.state IN
                        ('draft', 'confirmed', 'progress', 'to_close')))::date AS next_date_start,
                    COALESCE((MIN(mp.date_start) FILTER (WHERE mp.state IN
                        ('draft', 'confirmed', 'progress', 'to_close')))::date
                        < CURRENT_DATE, false) AS start_overdue,
                    MIN(mp.create_date)::date AS oldest_mo_date,
                    MAX(mp.create_date)::date AS newest_mo_date,
                    COALESCE(SUM(mp.product_qty) FILTER (WHERE mp.state != 'cancel'), 0) AS qty_total,
                    COUNT(*) FILTER (WHERE mp.state != 'cancel') AS mo_count,
                    COUNT(*) FILTER (WHERE mp.state IN
                        ('draft', 'confirmed', 'progress', 'to_close')) AS mo_todo_count,
                    COUNT(*) FILTER (WHERE mp.state = 'done') AS mo_done_count,
                    CASE WHEN COUNT(*) FILTER (WHERE mp.state != 'cancel') > 0
                         THEN ROUND(100.0 * COUNT(*) FILTER (WHERE mp.state = 'done')
                              / COUNT(*) FILTER (WHERE mp.state != 'cancel'))
                         ELSE 0 END AS progress,
                    CASE WHEN mp.vpa_so_group = 'Other Orders' THEN 1 ELSE 0 END AS sort_key
                FROM mrp_production mp
                LEFT JOIN (
                    -- one SO per (name, company): prevents double-counting MOs if
                    -- per-company sequences ever produce same-named Sales Orders
                    SELECT DISTINCT ON (name, company_id)
                           id, name, company_id, partner_id, client_order_ref,
                           user_id, amount_total, currency_id, commitment_date
                    FROM sale_order
                    ORDER BY name, company_id, id
                ) so ON so.name = mp.vpa_so_group AND so.company_id = mp.company_id
                WHERE mp.vpa_so_group != 'Other Orders'
                   OR mp.state IN ('draft', 'confirmed', 'progress', 'to_close')
                GROUP BY mp.vpa_so_group, mp.company_id
            )
        """)

    def action_view_mos(self):
        """Open the Manufacturing Orders belonging to this card."""
        self.ensure_one()
        domain = [('vpa_so_group', '=', self.name)]
        if not self.sale_id:
            # Other Orders card only tracks open MOs
            domain.append(('state', 'in', ('draft', 'confirmed', 'progress', 'to_close')))
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'mrp.production',
            'view_mode': 'list,kanban,form',
            'domain': domain,
            'context': {'default_origin': self.sale_id.name if self.sale_id else False},
        }

    def action_view_sale_order(self):
        """Open the linked Sales Order form."""
        self.ensure_one()
        if not self.sale_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'res_id': self.sale_id.id,
            'view_mode': 'form',
        }
