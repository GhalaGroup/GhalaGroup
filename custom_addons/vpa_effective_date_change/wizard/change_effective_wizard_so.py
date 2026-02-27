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

        old_date = self.original_date

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
        draft_invoices = so.invoice_ids.filtered(lambda inv: inv.state == 'draft')
        for invoice in draft_invoices:
            invoice.date = new_date.date() if hasattr(new_date, 'date') else new_date
            invoice.invoice_date = new_date.date() if hasattr(new_date, 'date') else new_date

        # 5. Log tracking message in chatter
        old_str = fields.Datetime.to_string(old_date)
        new_str = fields.Datetime.to_string(new_date)
        updated_docs = []
        if pickings:
            updated_docs.append(f"Deliveries: {', '.join(pickings.mapped('name'))}")
        if mos:
            updated_docs.append(f"Manufacturing Orders: {', '.join(mos.mapped('name'))}")
        if draft_invoices:
            updated_docs.append(f"Invoices: {', '.join(draft_invoices.mapped('name'))}")

        body = f"<b>Order Date Changed</b><br/>" \
               f"<b>From:</b> {old_str}<br/>" \
               f"<b>To:</b> {new_str}<br/>"
        if updated_docs:
            body += f"<br/><b>Related documents updated:</b><br/>" \
                    + "<br/>".join(updated_docs)

        so.message_post(body=body, subtype_xmlid='mail.mt_note')

        return {'type': 'ir.actions.act_window_close'}
