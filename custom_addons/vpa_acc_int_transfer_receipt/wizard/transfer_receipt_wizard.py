# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TransferReceiptWizard(models.TransientModel):
    _name = 'internal.transfer.receipt.wizard'
    _description = 'Internal Transfer Receipt Confirmation Wizard'

    transfer_id = fields.Many2one(
        'internal.transfer',
        string='Transfer',
        required=True,
        readonly=True,
    )
    transfer_name = fields.Char(
        related='transfer_id.name',
        string='Transfer Reference',
    )
    source_journal_id = fields.Many2one(
        related='transfer_id.source_journal_id',
        string='Source Journal',
    )
    destination_journal_id = fields.Many2one(
        related='transfer_id.destination_journal_id',
        string='Destination Journal',
    )
    currency_id = fields.Many2one(
        'res.currency',
        compute='_compute_currency',
        string='Currency',
    )
    expected_amount = fields.Monetary(
        string='Expected Amount',
        compute='_compute_expected_amount',
        currency_field='currency_id',
    )
    received_amount = fields.Monetary(
        string='Received Amount',
        required=True,
        currency_field='currency_id',
        help="Actual amount received in the destination account",
    )
    receipt_notes = fields.Text(
        string='Notes',
        help="Optional notes about the receipt confirmation",
    )
    amount_matches = fields.Boolean(
        compute='_compute_amount_matches',
        string='Amount Matches',
    )

    @api.depends('transfer_id')
    def _compute_currency(self):
        for wizard in self:
            transfer = wizard.transfer_id
            if transfer.is_multi_currency:
                wizard.currency_id = transfer.destination_currency_id
            else:
                wizard.currency_id = transfer.currency_id

    @api.depends('transfer_id')
    def _compute_expected_amount(self):
        for wizard in self:
            transfer = wizard.transfer_id
            if transfer.is_multi_currency:
                wizard.expected_amount = transfer.destination_amount
            else:
                wizard.expected_amount = transfer.amount

    @api.depends('received_amount', 'expected_amount')
    def _compute_amount_matches(self):
        for wizard in self:
            wizard.amount_matches = abs(
                wizard.received_amount - wizard.expected_amount
            ) < 0.01

    def action_confirm(self):
        """Confirm receipt of the transfer"""
        self.ensure_one()

        if self.received_amount <= 0:
            raise UserError(_('Received amount must be greater than zero.'))

        if not self.amount_matches:
            # Show warning if amounts don't match
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'internal.transfer.receipt.wizard',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    **self.env.context,
                    'show_amount_warning': True,
                },
            }

        return self._do_confirm()

    def action_confirm_anyway(self):
        """Confirm receipt even if amounts don't match"""
        return self._do_confirm()

    def _do_confirm(self):
        """Execute the receipt confirmation"""
        self.ensure_one()
        self.transfer_id.do_confirm_receipt(
            received_amount=self.received_amount,
            receipt_notes=self.receipt_notes,
        )
        return {'type': 'ir.actions.act_window_close'}
