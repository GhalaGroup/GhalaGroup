# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class ChangeEffectiveWizardSO(models.TransientModel):
    _name = "change.effective.wizard.so"
    _description = "Change Order Date - Sales Order"

    sale_order_id = fields.Many2one('sale.order', string="Sales Order", readonly=True)
    original_date = fields.Datetime(string="Current Order Date", readonly=True)
    effective_date = fields.Datetime(string="New Order Date", required=True,
                                     help="New date for the Sales Order and related documents")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_id'):
            so = self.env['sale.order'].browse(self.env.context.get('active_id'))
            res['sale_order_id'] = so.id
            res['original_date'] = so.date_order
            res['effective_date'] = so.date_order
        return res

    def update_effective_date(self):
        """Update the order date for the Sales Order and all related documents."""
        self.ensure_one()

        if not self.sale_order_id:
            return

        so = self.sale_order_id
        new_date = self.effective_date

        # 1. Update Sale Order date
        so.date_order = new_date

        # 2. Update related deliveries (non-done, non-cancelled)
        pickings = self.env['stock.picking'].search([
            ('origin', '=', so.name),
            ('state', 'not in', ('done', 'cancel')),
        ])
        for picking in pickings:
            picking.scheduled_date = new_date

        # 3. Update related Manufacturing Orders (non-done, non-cancelled)
        mos = self.env['mrp.production'].search([
            ('origin', '=', so.name),
            ('state', 'not in', ('done', 'cancel')),
        ])
        for mo in mos:
            mo.date_start = new_date
            mo.date_deadline = new_date

        # 4. Update related draft invoices
        for invoice in so.invoice_ids:
            if invoice.state == 'draft':
                invoice.date = new_date.date() if hasattr(new_date, 'date') else new_date
                invoice.invoice_date = new_date.date() if hasattr(new_date, 'date') else new_date

        return {'type': 'ir.actions.act_window_close'}
