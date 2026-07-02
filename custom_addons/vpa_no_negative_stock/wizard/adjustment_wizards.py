# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AdjustmentReasonWizard(models.TransientModel):
    _name = 'nns.adjustment.reason.wizard'
    _description = 'Inventory Adjustment Reason'

    quant_ids = fields.Many2many('stock.quant', string='Adjustments', readonly=True)
    summary = fields.Text(string='Adjustments', readonly=True)
    reason = fields.Text(string='Reason', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        quant_ids = self.env.context.get('default_quant_ids') or []
        quants = self.env['stock.quant'].browse(quant_ids)
        lines = []
        for q in quants:
            diff = q.inventory_quantity - q.quantity
            lines.append('%s @ %s: %s -> %s (%+g)' % (
                q.product_id.display_name, q.location_id.display_name,
                q.quantity, q.inventory_quantity, diff))
        res['summary'] = '\n'.join(lines)
        return res

    def action_submit(self):
        self.ensure_one()
        if not self.reason or not self.reason.strip():
            raise ValidationError(_('A reason is required to request an adjustment.'))
        quants = self.quant_ids or self.env['stock.quant'].browse(
            self.env.context.get('default_quant_ids') or [])
        requests = quants._nns_create_adjustment_requests(self.reason.strip())
        return {
            'name': _('Adjustment Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.adjustment.request',
            'view_mode': 'list,form',
            'domain': [('id', 'in', requests.ids)],
        }


class AdjustmentRejectWizard(models.TransientModel):
    _name = 'nns.adjustment.reject.wizard'
    _description = 'Reject Inventory Adjustment'

    request_id = fields.Many2one('stock.adjustment.request', required=True, readonly=True)
    reject_reason = fields.Text(string='Rejection Reason', required=True)

    def action_reject(self):
        self.ensure_one()
        if not self.reject_reason or not self.reject_reason.strip():
            raise ValidationError(_('A rejection reason is required.'))
        self.request_id._do_reject(self.reject_reason.strip())
        return {'type': 'ir.actions.act_window_close'}
