# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TransferResolveWizard(models.TransientModel):
    _name = 'internal.transfer.resolve.wizard'
    _description = 'Internal Transfer Dispute Resolution Wizard'

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
    original_amount = fields.Monetary(
        string='Original Amount',
        compute='_compute_original_amount',
        currency_field='currency_id',
    )
    dispute_reason = fields.Selection(
        related='transfer_id.dispute_reason',
        string='Dispute Reason',
    )
    dispute_notes = fields.Text(
        related='transfer_id.dispute_notes',
        string='Dispute Details',
    )
    disputed_amount = fields.Monetary(
        related='transfer_id.received_amount',
        string='Amount Reported by Custodian',
        currency_field='currency_id',
    )
    resolution = fields.Selection([
        ('adjusted', 'Adjust Amount & Complete'),
        ('cancelled', 'Cancel Transfer'),
        ('reconfirmed', 'Reconfirm Receipt (Original Amount)'),
    ], string='Resolution', required=True, default='reconfirmed')
    adjusted_amount = fields.Monetary(
        string='Adjusted Amount',
        currency_field='currency_id',
        help="New amount if adjusting the transfer",
    )
    resolution_notes = fields.Text(
        string='Resolution Notes',
        required=True,
        help="Explanation of the resolution",
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
    def _compute_original_amount(self):
        for wizard in self:
            transfer = wizard.transfer_id
            if transfer.is_multi_currency:
                wizard.original_amount = transfer.destination_amount
            else:
                wizard.original_amount = transfer.amount

    @api.onchange('resolution')
    def _onchange_resolution(self):
        """Pre-fill adjusted amount"""
        if self.resolution == 'adjusted':
            # Default to disputed amount if available
            self.adjusted_amount = self.disputed_amount or self.original_amount
        else:
            self.adjusted_amount = 0

    def action_resolve(self):
        """Resolve the dispute"""
        self.ensure_one()

        if not self.resolution_notes:
            raise UserError(_('Please provide resolution notes.'))

        if self.resolution == 'adjusted' and self.adjusted_amount <= 0:
            raise UserError(_('Adjusted amount must be greater than zero.'))

        self.transfer_id.do_resolve_dispute(
            resolution=self.resolution,
            notes=self.resolution_notes,
            adjusted_amount=self.adjusted_amount or 0,
        )
        return {'type': 'ir.actions.act_window_close'}
