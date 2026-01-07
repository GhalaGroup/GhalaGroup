# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TransferReassignWizard(models.TransientModel):
    _name = 'internal.transfer.reassign.wizard'
    _description = 'Internal Transfer Reassign Custodian Wizard'

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
    destination_journal_id = fields.Many2one(
        related='transfer_id.destination_journal_id',
        string='Destination Journal',
    )
    current_custodian_ids = fields.Many2many(
        related='transfer_id.destination_custodian_ids',
        string='Current Custodians',
    )
    new_custodian_id = fields.Many2one(
        'res.users',
        string='Reassign To',
        required=True,
        help="User to assign as the new recipient for this transfer",
    )
    reassign_notes = fields.Text(
        string='Reason for Reassignment',
        help="Explain why the transfer is being reassigned",
    )

    @api.onchange('transfer_id')
    def _onchange_transfer_id(self):
        """Set domain for new custodian"""
        if self.transfer_id:
            # Get all users who can potentially receive (custodians + backups + managers)
            company = self.transfer_id.company_id
            JournalCustodian = self.env['journal.custodian']

            custodian_record = JournalCustodian.search([
                ('journal_id', '=', self.transfer_id.destination_journal_id.id),
                ('company_id', '=', company.id),
                ('active', '=', True),
            ], limit=1)

            allowed_users = self.env['res.users']
            if custodian_record:
                allowed_users |= custodian_record.custodian_ids
                allowed_users |= custodian_record.backup_ids

            # Add transfer managers
            if company.transfer_manager_ids:
                allowed_users |= company.transfer_manager_ids

            if allowed_users:
                return {'domain': {'new_custodian_id': [('id', 'in', allowed_users.ids)]}}

        return {}

    def action_reassign(self):
        """Reassign the transfer to a new custodian"""
        self.ensure_one()

        if not self.new_custodian_id:
            raise UserError(_('Please select a user to reassign to.'))

        self.transfer_id.do_reassign_custodian(
            new_user_id=self.new_custodian_id.id,
            notes=self.reassign_notes,
        )
        return {'type': 'ir.actions.act_window_close'}
