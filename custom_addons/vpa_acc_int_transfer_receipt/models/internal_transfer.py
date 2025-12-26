# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InternalTransferReceipt(models.Model):
    _inherit = 'internal.transfer'

    # === EXTEND STATE MACHINE ===
    state = fields.Selection(
        selection_add=[
            ('pending_receipt', 'Pending Receipt'),
            ('received', 'Received'),
            ('disputed', 'Disputed'),
        ],
        ondelete={
            'pending_receipt': 'set default',
            'received': 'set default',
            'disputed': 'set default',
        },
    )

    # === RECEIPT TRACKING FIELDS ===
    received_by_id = fields.Many2one(
        'res.users',
        string='Received By',
        readonly=True,
        copy=False,
        tracking=True,
        help="Custodian who confirmed receipt of funds",
    )
    receipt_date = fields.Datetime(
        string='Receipt Confirmed On',
        readonly=True,
        copy=False,
    )
    receipt_notes = fields.Text(
        string='Receipt Notes',
        readonly=True,
        copy=False,
        tracking=True,
        help="Notes from custodian when confirming receipt",
    )
    received_amount = fields.Monetary(
        string='Received Amount',
        currency_field='destination_currency_id',
        readonly=True,
        copy=False,
        help="Actual amount confirmed by custodian",
    )

    # === DISPUTE FIELDS ===
    dispute_raised_by_id = fields.Many2one(
        'res.users',
        string='Dispute Raised By',
        readonly=True,
        copy=False,
        tracking=True,
    )
    dispute_date = fields.Datetime(
        string='Dispute Raised On',
        readonly=True,
        copy=False,
    )
    dispute_reason = fields.Selection([
        ('amount_mismatch', 'Amount Mismatch'),
        ('not_received', 'Funds Not Received'),
        ('partial_receipt', 'Partial Amount Received'),
        ('other', 'Other'),
    ], string='Dispute Reason', readonly=True, copy=False, tracking=True)
    dispute_notes = fields.Text(
        string='Dispute Details',
        readonly=True,
        copy=False,
        tracking=True,
    )

    # === DISPUTE RESOLUTION FIELDS ===
    dispute_resolved_by_id = fields.Many2one(
        'res.users',
        string='Dispute Resolved By',
        readonly=True,
        copy=False,
        tracking=True,
    )
    dispute_resolution_date = fields.Datetime(
        string='Dispute Resolved On',
        readonly=True,
        copy=False,
    )
    dispute_resolution = fields.Selection([
        ('adjusted', 'Amount Adjusted'),
        ('cancelled', 'Transfer Cancelled'),
        ('reconfirmed', 'Receipt Reconfirmed'),
    ], string='Resolution', readonly=True, copy=False, tracking=True)
    dispute_resolution_notes = fields.Text(
        string='Resolution Notes',
        readonly=True,
        copy=False,
        tracking=True,
    )

    # === REASSIGNMENT TRACKING ===
    reassigned_by_id = fields.Many2one(
        'res.users',
        string='Reassigned By',
        readonly=True,
        copy=False,
        tracking=True,
    )
    reassignment_date = fields.Datetime(
        string='Reassigned On',
        readonly=True,
        copy=False,
    )
    original_custodian_ids = fields.Many2many(
        'res.users',
        'internal_transfer_original_custodian_rel',
        'transfer_id',
        'user_id',
        string='Original Custodians',
        readonly=True,
        copy=False,
        help="Custodians originally assigned before reassignment",
    )

    # === PERMISSION FLAGS ===
    can_receive = fields.Boolean(
        compute='_compute_receipt_permissions',
        string='Can Confirm Receipt',
    )
    can_dispute = fields.Boolean(
        compute='_compute_receipt_permissions',
        string='Can Raise Dispute',
    )
    can_resolve_dispute = fields.Boolean(
        compute='_compute_receipt_permissions',
        string='Can Resolve Dispute',
    )

    # === CUSTODIAN INFO ===
    destination_custodian_ids = fields.Many2many(
        'res.users',
        compute='_compute_destination_custodians',
        string='Destination Custodians',
        help="Users who can confirm receipt for the destination journal",
    )
    has_custodian = fields.Boolean(
        compute='_compute_destination_custodians',
        string='Has Custodian',
        help="Whether the destination journal has custodians assigned",
    )

    # === RECEIPT CONFIRMATION ENABLED ===
    receipt_confirmation_enabled = fields.Boolean(
        compute='_compute_receipt_confirmation_enabled',
        string='Receipt Confirmation Enabled',
    )

    @api.depends('company_id')
    def _compute_receipt_confirmation_enabled(self):
        """Check if receipt confirmation is enabled for the company"""
        for transfer in self:
            transfer.receipt_confirmation_enabled = (
                transfer.company_id.enable_receipt_confirmation
            )

    @api.depends('destination_journal_id', 'company_id')
    def _compute_destination_custodians(self):
        """Get custodians for the destination journal"""
        JournalCustodian = self.env['journal.custodian']
        for transfer in self:
            if transfer.destination_journal_id and transfer.company_id:
                custodians = JournalCustodian.get_custodians_for_journal(
                    transfer.destination_journal_id.id,
                    transfer.company_id.id,
                )
                transfer.destination_custodian_ids = custodians
                transfer.has_custodian = bool(custodians)
            else:
                transfer.destination_custodian_ids = self.env['res.users']
                transfer.has_custodian = False

    @api.depends('destination_journal_id', 'company_id', 'state')
    @api.depends_context('uid')
    def _compute_receipt_permissions(self):
        """Compute receipt-related permission flags"""
        JournalCustodian = self.env['journal.custodian']
        for transfer in self:
            user = self.env.user
            company = transfer.company_id

            # Get custodians for destination journal
            if transfer.destination_journal_id:
                custodian_record = JournalCustodian.search([
                    ('journal_id', '=', transfer.destination_journal_id.id),
                    ('company_id', '=', company.id),
                    ('active', '=', True),
                ], limit=1)

                primary_custodians = custodian_record.custodian_ids if custodian_record else self.env['res.users']
                backup_custodians = custodian_record.backup_ids if custodian_record else self.env['res.users']
            else:
                primary_custodians = self.env['res.users']
                backup_custodians = self.env['res.users']

            # Get transfer managers as fallback
            transfer_managers = company.transfer_manager_ids

            # Can receive: custodian OR backup OR transfer manager (fallback)
            # NOTE: Transfer Managers can ONLY confirm if they are explicitly set
            # No automatic fallback to Account Managers
            can_receive = (
                user in primary_custodians or
                user in backup_custodians or
                (transfer_managers and user in transfer_managers)
            )

            # Can dispute: same as can_receive (custodians can dispute)
            can_dispute = can_receive

            # Can resolve dispute: originator OR receiver OR custodians
            can_resolve = (
                user == transfer.create_uid or
                user == transfer.received_by_id or
                can_receive
            )

            transfer.can_receive = can_receive
            transfer.can_dispute = can_dispute
            transfer.can_resolve_dispute = can_resolve

    # === OVERRIDE ACTION_APPROVE ===
    def action_approve(self):
        """
        Override approve to check if receipt confirmation is enabled.
        If enabled and custodian exists, move to pending_receipt instead of creating entries.
        """
        self.ensure_one()
        if self.state != 'submitted':
            raise UserError(_('Only submitted transfers can be approved.'))

        # Check approval permissions
        self._check_approval_permission()

        # Check if receipt confirmation is enabled
        if self.company_id.enable_receipt_confirmation:
            # Check if destination journal has custodian
            if self.has_custodian:
                # Move to pending_receipt state - don't create journal entries yet
                self.write({
                    'state': 'pending_receipt',
                    'approved_by_id': self.env.uid,
                    'approval_date': fields.Datetime.now(),
                })

                # Mark approval activity as done
                self.activity_feedback(['mail.mail_activity_data_todo'])

                # Notify custodians
                self._notify_destination_custodians()

                self.message_post(
                    body=_('Transfer approved by %s. Awaiting receipt confirmation from custodian.') % self.env.user.name,
                    subtype_xmlid='mail.mt_note',
                )
                return True

        # No receipt confirmation required - use original behavior
        return super().action_approve()

    def _notify_destination_custodians(self):
        """Create activities for destination custodians"""
        self.ensure_one()
        JournalCustodian = self.env['journal.custodian']

        # Get primary custodians
        custodians = JournalCustodian.get_primary_custodians_for_journal(
            self.destination_journal_id.id,
            self.company_id.id,
        )

        dest_amount = self.destination_amount if self.is_multi_currency else self.amount
        dest_currency = self.destination_currency_id if self.is_multi_currency else self.currency_id

        for user in custodians:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                summary=_('Receipt Confirmation Required'),
                note=_('Please confirm receipt of %s %s into %s for transfer %s.') % (
                    '{:,.2f}'.format(dest_amount),
                    dest_currency.name,
                    self.destination_journal_id.name,
                    self.name,
                ),
            )

    # === NEW WORKFLOW ACTIONS ===
    def action_confirm_receipt(self):
        """Open receipt confirmation wizard"""
        self.ensure_one()
        if self.state != 'pending_receipt':
            raise UserError(_('Only transfers pending receipt can be confirmed.'))

        if not self.can_receive:
            raise UserError(_('You are not authorized to confirm receipt for this transfer.'))

        dest_amount = self.destination_amount if self.is_multi_currency else self.amount

        return {
            'name': _('Confirm Receipt'),
            'type': 'ir.actions.act_window',
            'res_model': 'internal.transfer.receipt.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_transfer_id': self.id,
                'default_received_amount': dest_amount,
            },
        }

    def action_raise_dispute(self):
        """Open dispute wizard"""
        self.ensure_one()
        if self.state != 'pending_receipt':
            raise UserError(_('Only transfers pending receipt can be disputed.'))

        if not self.can_dispute:
            raise UserError(_('You are not authorized to raise a dispute for this transfer.'))

        return {
            'name': _('Raise Dispute'),
            'type': 'ir.actions.act_window',
            'res_model': 'internal.transfer.dispute.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_transfer_id': self.id},
        }

    def action_resolve_dispute(self):
        """Open dispute resolution wizard"""
        self.ensure_one()
        if self.state != 'disputed':
            raise UserError(_('Only disputed transfers can be resolved.'))

        if not self.can_resolve_dispute:
            raise UserError(_('You are not authorized to resolve this dispute.'))

        return {
            'name': _('Resolve Dispute'),
            'type': 'ir.actions.act_window',
            'res_model': 'internal.transfer.resolve.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_transfer_id': self.id},
        }

    def action_reassign_custodian(self):
        """Open reassignment wizard (Transfer Managers only)"""
        self.ensure_one()
        if self.state != 'pending_receipt':
            raise UserError(_('Only transfers pending receipt can be reassigned.'))

        if not self.can_manage:
            raise UserError(_('Only Transfer Managers can reassign custodians.'))

        return {
            'name': _('Reassign Custodian'),
            'type': 'ir.actions.act_window',
            'res_model': 'internal.transfer.reassign.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_transfer_id': self.id},
        }

    # === WIZARD CALLBACK METHODS ===
    def do_confirm_receipt(self, received_amount, receipt_notes=False):
        """Called by receipt wizard to complete confirmation"""
        self.ensure_one()
        if self.state != 'pending_receipt':
            raise UserError(_('Transfer is not in pending receipt state.'))

        # Create journal entries NOW
        self._create_journal_entries()

        # Auto-reconcile
        self._auto_reconcile()

        # Update transfer
        self.write({
            'state': 'received',
            'received_by_id': self.env.uid,
            'receipt_date': fields.Datetime.now(),
            'received_amount': received_amount,
            'receipt_notes': receipt_notes,
        })

        # Mark receipt activity as done
        self.activity_feedback(['mail.mail_activity_data_todo'])

        self.message_post(
            body=_('Receipt confirmed by %s. Amount: %s %s. Journal entries created.') % (
                self.env.user.name,
                '{:,.2f}'.format(received_amount),
                (self.destination_currency_id if self.is_multi_currency else self.currency_id).name,
            ),
            subtype_xmlid='mail.mt_note',
        )

    def do_raise_dispute(self, reason, notes, received_amount=0):
        """Called by dispute wizard to raise a dispute"""
        self.ensure_one()
        if self.state != 'pending_receipt':
            raise UserError(_('Transfer is not in pending receipt state.'))

        self.write({
            'state': 'disputed',
            'dispute_raised_by_id': self.env.uid,
            'dispute_date': fields.Datetime.now(),
            'dispute_reason': reason,
            'dispute_notes': notes,
            'received_amount': received_amount,
        })

        # Notify originator
        self._notify_dispute_raised()

        # Get dispute reason label
        reason_labels = dict(self._fields['dispute_reason'].selection)
        reason_label = reason_labels.get(reason, reason)

        self.message_post(
            body=_('Dispute raised by %s.\nReason: %s\nDetails: %s') % (
                self.env.user.name,
                reason_label,
                notes or _('No details provided'),
            ),
            subtype_xmlid='mail.mt_note',
        )

    def _notify_dispute_raised(self):
        """Notify originator about the dispute"""
        self.ensure_one()
        if self.create_uid and self.create_uid != self.env.user:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.create_uid.id,
                summary=_('Transfer Dispute Raised'),
                note=_('A dispute has been raised on transfer %s: %s') % (
                    self.name,
                    self.dispute_notes or self.dispute_reason,
                ),
            )

    def do_resolve_dispute(self, resolution, notes, adjusted_amount=0):
        """Called by resolve wizard to resolve a dispute"""
        self.ensure_one()
        if self.state != 'disputed':
            raise UserError(_('Transfer is not in disputed state.'))

        if resolution == 'cancelled':
            # Cancel the transfer
            self.write({
                'state': 'cancelled',
                'dispute_resolved_by_id': self.env.uid,
                'dispute_resolution_date': fields.Datetime.now(),
                'dispute_resolution': resolution,
                'dispute_resolution_notes': notes,
                'cancelled_by_id': self.env.uid,
                'cancellation_date': fields.Datetime.now(),
                'cancellation_reason': _('Cancelled due to dispute: %s') % notes,
            })
            self.activity_unlink(['mail.mail_activity_data_todo'])
            self.message_post(
                body=_('Dispute resolved by %s. Transfer cancelled.\nNotes: %s') % (
                    self.env.user.name,
                    notes or _('No notes'),
                ),
                subtype_xmlid='mail.mt_note',
            )

        elif resolution == 'adjusted':
            # Adjust amount and complete
            # Update the amount
            if adjusted_amount > 0:
                self.amount = adjusted_amount
                if self.is_multi_currency:
                    self.destination_amount = adjusted_amount * self.exchange_rate

            # Create journal entries with adjusted amount
            self._create_journal_entries()
            self._auto_reconcile()

            self.write({
                'state': 'received',
                'dispute_resolved_by_id': self.env.uid,
                'dispute_resolution_date': fields.Datetime.now(),
                'dispute_resolution': resolution,
                'dispute_resolution_notes': notes,
                'received_by_id': self.env.uid,
                'receipt_date': fields.Datetime.now(),
                'received_amount': adjusted_amount,
            })
            self.activity_feedback(['mail.mail_activity_data_todo'])
            self.message_post(
                body=_('Dispute resolved by %s. Amount adjusted to %s. Journal entries created.\nNotes: %s') % (
                    self.env.user.name,
                    '{:,.2f}'.format(adjusted_amount),
                    notes or _('No notes'),
                ),
                subtype_xmlid='mail.mt_note',
            )

        elif resolution == 'reconfirmed':
            # Reconfirm receipt with original amount
            self._create_journal_entries()
            self._auto_reconcile()

            dest_amount = self.destination_amount if self.is_multi_currency else self.amount
            self.write({
                'state': 'received',
                'dispute_resolved_by_id': self.env.uid,
                'dispute_resolution_date': fields.Datetime.now(),
                'dispute_resolution': resolution,
                'dispute_resolution_notes': notes,
                'received_by_id': self.env.uid,
                'receipt_date': fields.Datetime.now(),
                'received_amount': dest_amount,
            })
            self.activity_feedback(['mail.mail_activity_data_todo'])
            self.message_post(
                body=_('Dispute resolved by %s. Receipt reconfirmed. Journal entries created.\nNotes: %s') % (
                    self.env.user.name,
                    notes or _('No notes'),
                ),
                subtype_xmlid='mail.mt_note',
            )

    def do_reassign_custodian(self, new_user_id, notes=False):
        """Called by reassign wizard to reassign to a new custodian"""
        self.ensure_one()
        if self.state != 'pending_receipt':
            raise UserError(_('Transfer is not in pending receipt state.'))

        new_user = self.env['res.users'].browse(new_user_id)

        # Store original custodians if not already stored
        if not self.original_custodian_ids:
            self.original_custodian_ids = self.destination_custodian_ids

        # Cancel existing activities
        self.activity_unlink(['mail.mail_activity_data_todo'])

        # Create new activity for the new custodian
        dest_amount = self.destination_amount if self.is_multi_currency else self.amount
        dest_currency = self.destination_currency_id if self.is_multi_currency else self.currency_id

        self.activity_schedule(
            'mail.mail_activity_data_todo',
            user_id=new_user.id,
            summary=_('Receipt Confirmation Required (Reassigned)'),
            note=_('Please confirm receipt of %s %s into %s for transfer %s.\n\nReassigned by: %s\nReason: %s') % (
                '{:,.2f}'.format(dest_amount),
                dest_currency.name,
                self.destination_journal_id.name,
                self.name,
                self.env.user.name,
                notes or _('No reason provided'),
            ),
        )

        self.write({
            'reassigned_by_id': self.env.uid,
            'reassignment_date': fields.Datetime.now(),
        })

        self.message_post(
            body=_('Transfer reassigned by %s to %s.\nReason: %s') % (
                self.env.user.name,
                new_user.name,
                notes or _('No reason provided'),
            ),
            subtype_xmlid='mail.mt_note',
        )

    # === OVERRIDE LOCK/UNLOCK TO SUPPORT RECEIVED STATE ===
    def action_lock(self):
        """Override to allow locking for both approved and received states"""
        self.ensure_one()
        if self.state not in ('approved', 'received'):
            raise UserError(_('Only approved or received transfers can be locked.'))

        # Check manager permission
        self._check_manager_permission()

        self.write({'is_locked': True})
        self.message_post(
            body=_('Transfer locked by %s.') % self.env.user.name,
            subtype_xmlid='mail.mt_note',
        )

    def action_unlock(self):
        """Override to allow unlocking for both approved and received states"""
        self.ensure_one()
        if self.state not in ('approved', 'received'):
            raise UserError(_('Only approved or received transfers can be unlocked.'))

        # Check manager permission
        self._check_manager_permission()

        self.write({'is_locked': False})
        self.message_post(
            body=_('Transfer unlocked by %s.') % self.env.user.name,
            subtype_xmlid='mail.mt_note',
        )
