# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

import json
import base64
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class InternalTransferBackup(models.Model):
    """Model to handle backup and restore of internal transfers"""
    _name = 'internal.transfer.backup'
    _description = 'Internal Transfer Backup'
    _order = 'create_date desc'

    name = fields.Char(string='Backup Name', required=True)
    backup_date = fields.Datetime(string='Backup Date', default=fields.Datetime.now)
    transfer_count = fields.Integer(string='Transfer Count')
    backup_data = fields.Binary(string='Backup Data', attachment=True)
    backup_filename = fields.Char(string='Filename')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    notes = fields.Text(string='Notes')
    is_restored = fields.Boolean(string='Restored', default=False)
    restored_date = fields.Datetime(string='Restored Date')
    restored_by_id = fields.Many2one('res.users', string='Restored By')

    @api.model
    def create_backup(self, reason='Manual Backup'):
        """Create a backup of all internal transfers"""
        Transfer = self.env['internal.transfer']
        transfers = Transfer.search([])

        if not transfers:
            raise UserError(_('No transfers to backup.'))

        # Prepare backup data
        backup_data = {
            'version': '1.0',
            'backup_date': fields.Datetime.now().isoformat(),
            'reason': reason,
            'company_id': self.env.company.id,
            'company_name': self.env.company.name,
            'transfers': [],
        }

        for transfer in transfers:
            transfer_data = {
                'name': transfer.name,
                'date': transfer.date.isoformat() if transfer.date else None,
                'state': transfer.state,
                'amount': transfer.amount,
                'currency_id': transfer.currency_id.id,
                'currency_name': transfer.currency_id.name,
                'source_journal_id': transfer.source_journal_id.id,
                'source_journal_name': transfer.source_journal_id.name,
                'destination_journal_id': transfer.destination_journal_id.id,
                'destination_journal_name': transfer.destination_journal_id.name,
                'transfer_account_id': transfer.transfer_account_id.id,
                'transfer_account_code': transfer.transfer_account_id.code,
                'memo_type': transfer.memo_type,
                'memo': transfer.memo,
                'notes': transfer.notes,
                'is_locked': transfer.is_locked,
                'approver_id': transfer.approver_id.id if transfer.approver_id else None,
                'approver_login': transfer.approver_id.login if transfer.approver_id else None,
                'submitted_by_id': transfer.submitted_by_id.id if transfer.submitted_by_id else None,
                'submitted_by_login': transfer.submitted_by_id.login if transfer.submitted_by_id else None,
                'submit_date': transfer.submit_date.isoformat() if transfer.submit_date else None,
                'approved_by_id': transfer.approved_by_id.id if transfer.approved_by_id else None,
                'approved_by_login': transfer.approved_by_id.login if transfer.approved_by_id else None,
                'approval_date': transfer.approval_date.isoformat() if transfer.approval_date else None,
                'rejected_by_id': transfer.rejected_by_id.id if transfer.rejected_by_id else None,
                'rejected_by_login': transfer.rejected_by_id.login if transfer.rejected_by_id else None,
                'rejection_date': transfer.rejection_date.isoformat() if transfer.rejection_date else None,
                'rejection_reason': transfer.rejection_reason,
                'cancelled_by_id': transfer.cancelled_by_id.id if transfer.cancelled_by_id else None,
                'cancelled_by_login': transfer.cancelled_by_id.login if transfer.cancelled_by_id else None,
                'cancellation_date': transfer.cancellation_date.isoformat() if transfer.cancellation_date else None,
                'cancellation_reason': transfer.cancellation_reason,
                'company_id': transfer.company_id.id,
                # Multi-currency
                'is_multi_currency': transfer.is_multi_currency,
                'destination_currency_id': transfer.destination_currency_id.id if transfer.destination_currency_id else None,
                'destination_amount': transfer.destination_amount,
                'exchange_rate': transfer.exchange_rate,
            }
            backup_data['transfers'].append(transfer_data)

        # Convert to JSON and encode
        json_data = json.dumps(backup_data, indent=2, ensure_ascii=False)
        encoded_data = base64.b64encode(json_data.encode('utf-8'))

        # Create backup record
        backup_name = _('Transfer Backup - %s') % datetime.now().strftime('%Y-%m-%d %H:%M')
        filename = 'transfer_backup_%s.json' % datetime.now().strftime('%Y%m%d_%H%M%S')

        backup = self.create({
            'name': backup_name,
            'transfer_count': len(transfers),
            'backup_data': encoded_data,
            'backup_filename': filename,
            'notes': reason,
        })

        return backup

    def action_restore(self):
        """Restore transfers from backup"""
        self.ensure_one()

        if not self.backup_data:
            raise UserError(_('No backup data found.'))

        # Decode and parse JSON
        json_data = base64.b64decode(self.backup_data).decode('utf-8')
        backup_data = json.loads(json_data)

        Transfer = self.env['internal.transfer']
        restored_count = 0
        skipped_count = 0
        errors = []

        for transfer_data in backup_data.get('transfers', []):
            try:
                # Check if transfer already exists
                existing = Transfer.search([('name', '=', transfer_data['name'])], limit=1)
                if existing:
                    skipped_count += 1
                    continue

                # Find related records by ID first, then by name/login
                currency = self._find_currency(transfer_data)
                source_journal = self._find_journal(transfer_data, 'source')
                dest_journal = self._find_journal(transfer_data, 'destination')
                transfer_account = self._find_account(transfer_data)

                if not all([currency, source_journal, dest_journal, transfer_account]):
                    errors.append(_('Transfer %s: Missing required records (journal/currency/account)') % transfer_data['name'])
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

                # Add user references if found
                if transfer_data.get('approver_login'):
                    user = self.env['res.users'].search([('login', '=', transfer_data['approver_login'])], limit=1)
                    if user:
                        vals['approver_id'] = user.id

                if transfer_data.get('submitted_by_login'):
                    user = self.env['res.users'].search([('login', '=', transfer_data['submitted_by_login'])], limit=1)
                    if user:
                        vals['submitted_by_id'] = user.id
                        vals['submit_date'] = transfer_data.get('submit_date')

                if transfer_data.get('approved_by_login'):
                    user = self.env['res.users'].search([('login', '=', transfer_data['approved_by_login'])], limit=1)
                    if user:
                        vals['approved_by_id'] = user.id
                        vals['approval_date'] = transfer_data.get('approval_date')

                if transfer_data.get('rejected_by_login'):
                    user = self.env['res.users'].search([('login', '=', transfer_data['rejected_by_login'])], limit=1)
                    if user:
                        vals['rejected_by_id'] = user.id
                        vals['rejection_date'] = transfer_data.get('rejection_date')
                        vals['rejection_reason'] = transfer_data.get('rejection_reason')

                if transfer_data.get('cancelled_by_login'):
                    user = self.env['res.users'].search([('login', '=', transfer_data['cancelled_by_login'])], limit=1)
                    if user:
                        vals['cancelled_by_id'] = user.id
                        vals['cancellation_date'] = transfer_data.get('cancellation_date')
                        vals['cancellation_reason'] = transfer_data.get('cancellation_reason')

                # Create transfer (bypass sequence for restored records)
                Transfer.with_context(restore_mode=True).create(vals)
                restored_count += 1

            except Exception as e:
                errors.append(_('Transfer %s: %s') % (transfer_data.get('name', 'Unknown'), str(e)))

        # Mark as restored
        self.write({
            'is_restored': True,
            'restored_date': fields.Datetime.now(),
            'restored_by_id': self.env.uid,
        })

        # Prepare message
        message = _('Restore completed:\n- Restored: %d transfers\n- Skipped (already exist): %d') % (restored_count, skipped_count)
        if errors:
            message += _('\n\nErrors:\n') + '\n'.join(errors[:10])
            if len(errors) > 10:
                message += _('\n... and %d more errors') % (len(errors) - 10)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Restore Complete'),
                'message': message,
                'type': 'success' if not errors else 'warning',
                'sticky': True,
            }
        }

    def _find_currency(self, transfer_data):
        """Find currency by ID or name"""
        Currency = self.env['res.currency']
        currency = Currency.browse(transfer_data.get('currency_id'))
        if currency.exists():
            return currency
        return Currency.search([('name', '=', transfer_data.get('currency_name'))], limit=1)

    def _find_journal(self, transfer_data, journal_type):
        """Find journal by ID or name"""
        Journal = self.env['account.journal']
        field_id = f'{journal_type}_journal_id'
        field_name = f'{journal_type}_journal_name'

        journal = Journal.browse(transfer_data.get(field_id))
        if journal.exists():
            return journal
        return Journal.search([('name', '=', transfer_data.get(field_name))], limit=1)

    def _find_account(self, transfer_data):
        """Find account by ID or code"""
        Account = self.env['account.account']
        account = Account.browse(transfer_data.get('transfer_account_id'))
        if account.exists():
            return account
        return Account.search([('code', '=', transfer_data.get('transfer_account_code'))], limit=1)

    def action_download(self):
        """Download backup file"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/backup_data/%s?download=true' % (
                self._name.replace('.', '_'),
                self.id,
                self.backup_filename or 'backup.json'
            ),
            'target': 'self',
        }
