# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Software Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

import json
import base64
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


def pre_uninstall_hook(env):
    """
    Hook called before module uninstallation.
    Creates an automatic backup of all internal transfers to prevent data loss.
    The backup is stored in ir.attachment so it survives the uninstall.
    """
    _logger.info("VPA Internal Transfer: Starting pre-uninstall backup...")

    Transfer = env['internal.transfer']
    transfers = Transfer.search([])

    if not transfers:
        _logger.info("VPA Internal Transfer: No transfers to backup.")
        return

    # Prepare backup data
    backup_data = {
        'version': '1.0',
        'backup_date': datetime.now().isoformat(),
        'reason': 'Pre-uninstall automatic backup',
        'transfer_count': len(transfers),
        'transfers': [],
    }

    for transfer in transfers:
        try:
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
                'company_name': transfer.company_id.name,
                # Multi-currency
                'is_multi_currency': transfer.is_multi_currency,
                'destination_currency_id': transfer.destination_currency_id.id if transfer.destination_currency_id else None,
                'destination_currency_name': transfer.destination_currency_id.name if transfer.destination_currency_id else None,
                'destination_amount': transfer.destination_amount,
                'exchange_rate': transfer.exchange_rate,
            }
            backup_data['transfers'].append(transfer_data)
        except Exception as e:
            _logger.warning("VPA Internal Transfer: Error backing up transfer %s: %s", transfer.name, str(e))

    # Convert to JSON and encode
    json_data = json.dumps(backup_data, indent=2, ensure_ascii=False)
    encoded_data = base64.b64encode(json_data.encode('utf-8'))

    # Store in ir.attachment (survives module uninstall)
    filename = 'vpa_internal_transfer_backup_%s.json' % datetime.now().strftime('%Y%m%d_%H%M%S')

    env['ir.attachment'].create({
        'name': filename,
        'type': 'binary',
        'datas': encoded_data,
        'mimetype': 'application/json',
        'description': 'VPA Internal Transfer - Automatic backup before uninstall (%d transfers)' % len(transfers),
        'res_model': 'ir.module.module',
        'res_id': 0,  # Not linked to specific record
    })

    _logger.info("VPA Internal Transfer: Backup completed. %d transfers saved to attachment: %s", len(transfers), filename)


def post_init_hook(env):
    """
    Hook called after module installation.
    Checks for existing backups and notifies user.
    """
    _logger.info("VPA Internal Transfer: Checking for existing backups...")

    # Search for backup attachments
    backups = env['ir.attachment'].search([
        ('name', 'like', 'vpa_internal_transfer_backup_'),
        ('mimetype', '=', 'application/json'),
    ], order='create_date desc')

    if backups:
        _logger.info(
            "VPA Internal Transfer: Found %d backup(s). "
            "Go to Accounting > Configuration > Internal Transfer Backups to restore.",
            len(backups)
        )
