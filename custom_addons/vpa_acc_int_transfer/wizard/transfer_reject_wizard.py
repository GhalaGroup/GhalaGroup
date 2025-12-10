# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Software Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class InternalTransferRejectWizard(models.TransientModel):
    _name = 'internal.transfer.reject.wizard'
    _description = 'Reject Internal Transfer Wizard'

    transfer_id = fields.Many2one(
        'internal.transfer',
        string='Transfer',
        required=True,
    )
    transfer_name = fields.Char(
        related='transfer_id.name',
        string='Transfer Reference',
        readonly=True,
    )
    transfer_amount = fields.Monetary(
        related='transfer_id.amount',
        string='Amount',
        readonly=True,
    )
    currency_id = fields.Many2one(
        related='transfer_id.currency_id',
        readonly=True,
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        required=True,
        help='Please provide a reason for rejecting this transfer',
    )

    def action_reject(self):
        """Reject the transfer with reason"""
        self.ensure_one()
        self.transfer_id.write({
            'state': 'rejected',
            'rejected_by_id': self.env.uid,
            'rejection_reason': self.rejection_reason,
            'rejection_date': fields.Datetime.now(),
        })
        self.transfer_id.message_post(
            body=_('Transfer rejected by %s.<br/><b>Reason:</b> %s') % (
                self.env.user.name, self.rejection_reason
            ),
            subtype_xmlid='mail.mt_note',
        )
        return {'type': 'ir.actions.act_window_close'}
