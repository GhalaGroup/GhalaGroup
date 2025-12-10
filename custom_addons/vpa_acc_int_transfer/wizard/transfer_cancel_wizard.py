# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Software Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class InternalTransferCancelWizard(models.TransientModel):
    _name = 'internal.transfer.cancel.wizard'
    _description = 'Cancel Internal Transfer Wizard'

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
    cancellation_reason = fields.Text(
        string='Cancellation Reason',
        required=True,
        help='Please provide a reason for cancelling this transfer',
    )
    create_reversal = fields.Boolean(
        string='Create Reversal Entries',
        default=True,
        help='Create reversal journal entries (only for approved transfers)',
    )
    transfer_state = fields.Selection(
        related='transfer_id.state',
        string='Current State',
    )
    has_journal_entries = fields.Boolean(
        compute='_compute_has_journal_entries',
    )

    @api.depends('transfer_id')
    def _compute_has_journal_entries(self):
        for wizard in self:
            wizard.has_journal_entries = bool(
                wizard.transfer_id.source_move_id or wizard.transfer_id.destination_move_id
            )

    def action_cancel(self):
        """Cancel the transfer with optional reversal"""
        self.ensure_one()
        transfer = self.transfer_id

        # Create reversal entries if approved and has journal entries
        if transfer.state == 'approved' and self.has_journal_entries and self.create_reversal:
            transfer._create_reversal_entries(self.cancellation_reason)

        transfer.write({
            'state': 'cancelled',
            'cancelled_by_id': self.env.uid,
            'cancellation_reason': self.cancellation_reason,
            'cancellation_date': fields.Datetime.now(),
        })

        body = _('Transfer cancelled by %s.<br/><b>Reason:</b> %s') % (
            self.env.user.name, self.cancellation_reason
        )
        if self.has_journal_entries and self.create_reversal:
            body += _('<br/><i>Reversal entries created.</i>')

        transfer.message_post(
            body=body,
            subtype_xmlid='mail.mt_note',
        )
        return {'type': 'ir.actions.act_window_close'}
