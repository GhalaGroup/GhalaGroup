# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Software Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

import json
import base64
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RestoreBackupWizard(models.TransientModel):
    _name = 'internal.transfer.restore.wizard'
    _description = 'Restore Internal Transfer Backup'

    backup_source = fields.Selection([
        ('attachment', 'From Automatic Backup'),
        ('file', 'From Uploaded File'),
    ], string='Backup Source', default='attachment', required=True)

    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Select Backup',
        domain="[('name', 'like', 'vpa_internal_transfer_backup_'), ('mimetype', '=', 'application/json')]",
    )

    upload_file = fields.Binary(string='Upload Backup File')
    upload_filename = fields.Char(string='Filename')

    preview_info = fields.Text(string='Backup Info', readonly=True)

    @api.onchange('backup_source', 'attachment_id', 'upload_file')
    def _onchange_backup(self):
        """Preview backup contents"""
        self.preview_info = ''

        backup_data = None

        if self.backup_source == 'attachment' and self.attachment_id:
            try:
                json_data = base64.b64decode(self.attachment_id.datas).decode('utf-8')
                backup_data = json.loads(json_data)
            except Exception:
                self.preview_info = _('Error reading backup file')
                return

        elif self.backup_source == 'file' and self.upload_file:
            try:
                json_data = base64.b64decode(self.upload_file).decode('utf-8')
                backup_data = json.loads(json_data)
            except Exception:
                self.preview_info = _('Error reading uploaded file')
                return

        if backup_data:
            transfers = backup_data.get('transfers', [])
            info = [
                _('Backup Date: %s') % backup_data.get('backup_date', 'Unknown'),
                _('Reason: %s') % backup_data.get('reason', 'Unknown'),
                _('Total Transfers: %d') % len(transfers),
                '',
                _('By State:'),
            ]

            # Count by state
            states = {}
            for t in transfers:
                state = t.get('state', 'unknown')
                states[state] = states.get(state, 0) + 1

            for state, count in sorted(states.items()):
                info.append(_('  - %s: %d') % (state.title(), count))

            self.preview_info = '\n'.join(info)

    def action_restore(self):
        """Restore from selected backup"""
        self.ensure_one()

        # Get backup data
        if self.backup_source == 'attachment':
            if not self.attachment_id:
                raise UserError(_('Please select a backup to restore.'))
            json_data = base64.b64decode(self.attachment_id.datas).decode('utf-8')
        else:
            if not self.upload_file:
                raise UserError(_('Please upload a backup file.'))
            json_data = base64.b64decode(self.upload_file).decode('utf-8')

        backup_data = json.loads(json_data)
        transfers_data = backup_data.get('transfers', [])

        if not transfers_data:
            raise UserError(_('No transfers found in backup.'))

        Transfer = self.env['internal.transfer']
        restored_count = 0
        skipped_count = 0
        errors = []

        for transfer_data in transfers_data:
            try:
                # Check if transfer already exists
                existing = Transfer.search([('name', '=', transfer_data['name'])], limit=1)
                if existing:
                    skipped_count += 1
                    continue

                # Find related records
                currency = self._find_record('res.currency', transfer_data.get('currency_id'), transfer_data.get('currency_name'), 'name')
                source_journal = self._find_record('account.journal', transfer_data.get('source_journal_id'), transfer_data.get('source_journal_name'), 'name')
                dest_journal = self._find_record('account.journal', transfer_data.get('destination_journal_id'), transfer_data.get('destination_journal_name'), 'name')
                transfer_account = self._find_record('account.account', transfer_data.get('transfer_account_id'), transfer_data.get('transfer_account_code'), 'code')

                if not all([currency, source_journal, dest_journal, transfer_account]):
                    missing = []
                    if not currency:
                        missing.append('currency')
                    if not source_journal:
                        missing.append('source journal')
                    if not dest_journal:
                        missing.append('destination journal')
                    if not transfer_account:
                        missing.append('transfer account')
                    errors.append(_('%s: Missing %s') % (transfer_data['name'], ', '.join(missing)))
                    continue

                # Prepare values
                vals = {
                    'name': transfer_data['name'],
                    'date': transfer_data['date'],
                    'state': transfer_data['state'],
                    'amount': transfer_data['amount'],
                    'currency_id': currency.id,
                    'source_journal_id': source_journal.id,
                    'destination_journal_id': dest_journal.id,
                    'transfer_account_id': transfer_account.id,
                    'memo_type': transfer_data.get('memo_type', 'internal_transfer'),
                    'memo': transfer_data.get('memo'),
                    'notes': transfer_data.get('notes'),
                    'is_locked': transfer_data.get('is_locked', False),
                    'company_id': self.env.company.id,
                }

                # Add user references
                self._add_user_field(vals, transfer_data, 'approver')
                self._add_user_field(vals, transfer_data, 'submitted_by', date_field='submit_date')
                self._add_user_field(vals, transfer_data, 'approved_by', date_field='approval_date')
                self._add_user_field(vals, transfer_data, 'rejected_by', date_field='rejection_date', reason_field='rejection_reason')
                self._add_user_field(vals, transfer_data, 'cancelled_by', date_field='cancellation_date', reason_field='cancellation_reason')

                # Create transfer
                Transfer.with_context(restore_mode=True).create(vals)
                restored_count += 1

            except Exception as e:
                errors.append(_('%s: %s') % (transfer_data.get('name', 'Unknown'), str(e)))

        # Build result message
        message_parts = [
            _('Restored: %d transfers') % restored_count,
            _('Skipped (already exist): %d') % skipped_count,
        ]
        if errors:
            message_parts.append(_('Errors: %d') % len(errors))

        message = '\n'.join(message_parts)
        msg_type = 'success' if not errors else 'warning'

        if errors:
            message += '\n\n' + _('Error details:\n') + '\n'.join(errors[:5])
            if len(errors) > 5:
                message += _('\n... and %d more') % (len(errors) - 5)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Restore Complete'),
                'message': message,
                'type': msg_type,
                'sticky': True,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def _find_record(self, model, record_id, fallback_value, fallback_field):
        """Find record by ID or fallback field"""
        Model = self.env[model]
        if record_id:
            record = Model.browse(record_id)
            if record.exists():
                return record
        if fallback_value:
            return Model.search([(fallback_field, '=', fallback_value)], limit=1)
        return None

    def _add_user_field(self, vals, data, field_prefix, date_field=None, reason_field=None):
        """Add user-related fields to vals dict"""
        login = data.get(f'{field_prefix}_login')
        if login:
            user = self.env['res.users'].search([('login', '=', login)], limit=1)
            if user:
                vals[f'{field_prefix}_id'] = user.id
                if date_field and data.get(date_field):
                    vals[date_field] = data[date_field]
                if reason_field and data.get(reason_field):
                    vals[reason_field] = data[reason_field]
