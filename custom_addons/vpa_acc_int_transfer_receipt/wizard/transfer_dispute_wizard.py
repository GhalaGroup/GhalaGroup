# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TransferDisputeWizard(models.TransientModel):
    _name = 'internal.transfer.dispute.wizard'
    _description = 'Internal Transfer Dispute Wizard'

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
    dispute_reason = fields.Selection([
        ('amount_mismatch', 'Amount Mismatch'),
        ('not_received', 'Funds Not Received'),
        ('partial_receipt', 'Partial Amount Received'),
        ('other', 'Other'),
    ], string='Reason', required=True, default='not_received')
    received_amount = fields.Monetary(
        string='Actual Amount Received',
        currency_field='currency_id',
        help="If partial amount received, enter the actual amount here",
    )
    dispute_notes = fields.Text(
        string='Details',
        required=True,
        help="Provide details about the dispute",
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

    @api.onchange('dispute_reason')
    def _onchange_dispute_reason(self):
        """Pre-fill notes based on reason"""
        if self.dispute_reason == 'not_received':
            self.received_amount = 0
        elif self.dispute_reason == 'amount_mismatch' and not self.dispute_notes:
            self.dispute_notes = _('Amount received does not match expected amount.')
        elif self.dispute_reason == 'partial_receipt' and not self.dispute_notes:
            self.dispute_notes = _('Only partial amount was received.')

    def action_raise_dispute(self):
        """Raise the dispute"""
        self.ensure_one()

        if not self.dispute_notes:
            raise UserError(_('Please provide details about the dispute.'))

        self.transfer_id.do_raise_dispute(
            reason=self.dispute_reason,
            notes=self.dispute_notes,
            received_amount=self.received_amount or 0,
        )
        return {'type': 'ir.actions.act_window_close'}
