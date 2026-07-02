# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class NegativeOverrideWizard(models.TransientModel):
    _name = 'nns.override.wizard'
    _description = 'Override Negative Stock'

    res_model = fields.Char(string='Document Model', required=True, readonly=True)
    res_id = fields.Integer(string='Document ID', required=True, readonly=True)
    document_name = fields.Char(string='Document', readonly=True)
    reason = fields.Text(string='Reason', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        if model and active_id:
            record = self.env[model].browse(active_id)
            res.update({
                'res_model': model,
                'res_id': active_id,
                'document_name': record.display_name,
            })
        return res

    def action_confirm(self):
        self.ensure_one()
        if not self.env.user.has_group('vpa_no_negative_stock.group_stock_sentinel_override'):
            raise UserError(_(
                'Only an Inventory Manager with Stock Sentinel override rights can '
                'force a negative-stock operation.'))
        if not self.reason or not self.reason.strip():
            raise ValidationError(_('A reason is required to override negative stock.'))

        record = self.env[self.res_model].browse(self.res_id)
        if not record.exists():
            raise UserError(_('The document to validate no longer exists.'))

        record = record.with_context(
            nns_override_ok=True,
            nns_override_reason=self.reason.strip(),
            nns_document_ref=record.display_name,
        )

        # Re-run the document's own validation with the override context.
        if self.res_model == 'stock.picking':
            return record.button_validate()
        if self.res_model == 'stock.scrap':
            return record.action_validate()
        if self.res_model == 'mrp.production':
            return record.button_mark_done()
        # Fallback: generic done action if present.
        if hasattr(record, 'button_validate'):
            return record.button_validate()
        raise UserError(_('Override is not supported for this document type.'))
