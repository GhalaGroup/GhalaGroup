# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Software Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class InternalTransfer(models.Model):
    _name = 'internal.transfer'
    _description = 'Internal Account Transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _rec_name = 'name'

    # === IDENTIFICATION ===
    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True,
    )

    # === STATE MACHINE ===
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True, copy=False)

    # === DATES ===
    date = fields.Date(
        string='Transfer Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    create_date = fields.Datetime(string='Created On', readonly=True)
    submit_date = fields.Datetime(string='Submitted On', readonly=True, copy=False)
    approval_date = fields.Datetime(string='Approved On', readonly=True, copy=False)

    # === SOURCE ACCOUNT ===
    source_journal_id = fields.Many2one(
        'account.journal',
        string='From Journal',
        required=True,
        tracking=True,
        domain="[('type', 'in', ['bank', 'cash']), ('company_id', '=', company_id)]",
    )
    source_account_id = fields.Many2one(
        'account.account',
        string='From Account',
        compute='_compute_source_account',
        store=True,
    )

    # === DESTINATION ACCOUNT ===
    destination_journal_id = fields.Many2one(
        'account.journal',
        string='To Journal',
        required=True,
        tracking=True,
        domain="[('type', 'in', ['bank', 'cash']), ('company_id', '=', company_id)]",
    )
    destination_account_id = fields.Many2one(
        'account.account',
        string='To Account',
        compute='_compute_destination_account',
        store=True,
    )

    # === INTERMEDIATE ACCOUNT ===
    transfer_account_id = fields.Many2one(
        'account.account',
        string='Internal Transfer Account',
        required=True,
        tracking=True,
        default=lambda self: self.env.company.transfer_account_id,
        domain="[('account_type', '=', 'asset_current'), ('reconcile', '=', True)]",
        help='Intermediate account used for proper double-entry accounting. Uses company default from Accounting Settings.',
    )

    # === AMOUNTS ===
    amount = fields.Monetary(
        string='Amount',
        required=True,
        tracking=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        tracking=True,
    )

    # === MULTI-CURRENCY SUPPORT ===
    destination_currency_id = fields.Many2one(
        'res.currency',
        string='Destination Currency',
        compute='_compute_destination_currency',
        store=True,
    )
    destination_amount = fields.Monetary(
        string='Destination Amount',
        currency_field='destination_currency_id',
        compute='_compute_destination_amount',
        store=True,
        readonly=False,
        help='Amount in destination currency (auto-calculated, can be overridden)',
    )
    exchange_rate = fields.Float(
        string='Exchange Rate',
        digits=(12, 6),
        compute='_compute_exchange_rate',
        store=True,
        readonly=False,
    )
    is_multi_currency = fields.Boolean(
        string='Multi-Currency Transfer',
        compute='_compute_is_multi_currency',
        store=True,
    )

    # === COMPANY ===
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )

    # === DESCRIPTION ===
    memo_type = fields.Selection([
        ('internal_transfer', 'Internal Transfer'),
        ('bank_deposit', 'Bank Deposit'),
        ('cash_withdrawal', 'Cash Withdrawal'),
        ('petty_cash', 'Petty Cash Replenishment'),
        ('fund_transfer', 'Fund Transfer'),
        ('custom', 'Custom Memo'),
    ], string='Memo Type', default='internal_transfer',
       help='Select a predefined memo type or choose Custom to write your own.')
    memo = fields.Char(
        string='Memo',
        tracking=True,
        compute='_compute_memo',
        store=True,
        readonly=False,
        help='Auto-generated based on memo type. Can be manually overridden when Custom is selected.',
    )
    notes = fields.Text(
        string='Internal Notes',
        tracking=True,
    )

    # === APPROVER SELECTION ===
    approver_id = fields.Many2one(
        'res.users',
        string='Approver',
        tracking=True,
        help='Select the user who should approve this transfer. They will receive an activity notification.',
    )

    # === APPROVAL TRACKING ===
    submitted_by_id = fields.Many2one(
        'res.users',
        string='Submitted By',
        readonly=True,
        copy=False,
        tracking=True,
    )
    approved_by_id = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        copy=False,
        tracking=True,
    )
    rejected_by_id = fields.Many2one(
        'res.users',
        string='Rejected By',
        readonly=True,
        copy=False,
        tracking=True,
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        readonly=True,
        copy=False,
        tracking=True,
    )
    rejection_date = fields.Datetime(
        string='Rejected On',
        readonly=True,
        copy=False,
    )

    # === APPROVAL LEVEL ===
    required_approval_level = fields.Selection([
        ('manager', 'Manager'),
        ('admin', 'Administrator'),
    ], string='Required Approval Level', compute='_compute_required_approval_level', store=True)

    # === JOURNAL ENTRIES ===
    source_move_id = fields.Many2one(
        'account.move',
        string='Source Journal Entry',
        readonly=True,
        copy=False,
    )
    destination_move_id = fields.Many2one(
        'account.move',
        string='Destination Journal Entry',
        readonly=True,
        copy=False,
    )
    move_count = fields.Integer(
        string='Journal Entry Count',
        compute='_compute_move_count',
    )

    # === ATTACHMENTS ===
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'internal_transfer_attachment_rel',
        'transfer_id',
        'attachment_id',
        string='Attachments',
    )
    attachment_count = fields.Integer(
        string='Attachment Count',
        compute='_compute_attachment_count',
    )

    # === CANCELLATION ===
    cancelled_by_id = fields.Many2one(
        'res.users',
        string='Cancelled By',
        readonly=True,
        copy=False,
        tracking=True,
    )
    cancellation_reason = fields.Text(
        string='Cancellation Reason',
        readonly=True,
        copy=False,
        tracking=True,
    )
    cancellation_date = fields.Datetime(
        string='Cancelled On',
        readonly=True,
        copy=False,
    )

    # === COMPUTED METHODS ===
    @api.depends('memo_type', 'source_journal_id', 'destination_journal_id', 'amount', 'date')
    def _compute_memo(self):
        """Generate memo based on selected memo type"""
        memo_templates = {
            'internal_transfer': _('Internal Transfer from {source} to {destination}'),
            'bank_deposit': _('Bank Deposit to {destination} from {source}'),
            'cash_withdrawal': _('Cash Withdrawal from {source} to {destination}'),
            'petty_cash': _('Petty Cash Replenishment - {source} to {destination}'),
            'fund_transfer': _('Fund Transfer: {source} → {destination}'),
        }
        for transfer in self:
            # Skip if custom memo type - user will enter manually
            if transfer.memo_type == 'custom':
                if not transfer.memo:
                    transfer.memo = ''
                continue

            if transfer.source_journal_id and transfer.destination_journal_id:
                template = memo_templates.get(
                    transfer.memo_type,
                    _('Internal Transfer from {source} to {destination}')
                )
                try:
                    transfer.memo = template.format(
                        source=transfer.source_journal_id.name or '',
                        destination=transfer.destination_journal_id.name or '',
                        user=self.env.user.name or '',
                        amount='{:,.2f}'.format(transfer.amount or 0),
                        date=str(transfer.date or fields.Date.today()),
                    )
                except (KeyError, ValueError):
                    transfer.memo = _('Transfer from %s to %s') % (
                        transfer.source_journal_id.name,
                        transfer.destination_journal_id.name,
                    )
            elif not transfer.memo:
                transfer.memo = False

    @api.depends('source_journal_id')
    def _compute_source_account(self):
        for transfer in self:
            transfer.source_account_id = transfer.source_journal_id.default_account_id

    @api.depends('destination_journal_id')
    def _compute_destination_account(self):
        for transfer in self:
            transfer.destination_account_id = transfer.destination_journal_id.default_account_id

    @api.depends('destination_journal_id', 'destination_journal_id.currency_id', 'company_id')
    def _compute_destination_currency(self):
        for transfer in self:
            transfer.destination_currency_id = (
                transfer.destination_journal_id.currency_id or
                transfer.company_id.currency_id
            )

    @api.depends('currency_id', 'destination_currency_id')
    def _compute_is_multi_currency(self):
        for transfer in self:
            transfer.is_multi_currency = (
                transfer.currency_id and
                transfer.destination_currency_id and
                transfer.currency_id != transfer.destination_currency_id
            )

    @api.depends('amount', 'currency_id', 'destination_currency_id', 'date', 'company_id')
    def _compute_exchange_rate(self):
        for transfer in self:
            if transfer.is_multi_currency and transfer.amount:
                rate = transfer.currency_id._get_conversion_rate(
                    transfer.currency_id,
                    transfer.destination_currency_id,
                    transfer.company_id,
                    transfer.date or fields.Date.today()
                )
                transfer.exchange_rate = rate
            else:
                transfer.exchange_rate = 1.0

    @api.depends('amount', 'exchange_rate', 'is_multi_currency')
    def _compute_destination_amount(self):
        for transfer in self:
            if transfer.is_multi_currency:
                transfer.destination_amount = transfer.amount * transfer.exchange_rate
            else:
                transfer.destination_amount = transfer.amount

    @api.depends('amount', 'company_id')
    def _compute_required_approval_level(self):
        """Determine required approval level based on amount thresholds"""
        for transfer in self:
            threshold = self.env['internal.transfer.threshold'].search([
                ('company_id', '=', transfer.company_id.id),
                ('active', '=', True),
                ('min_amount', '<=', transfer.amount),
                '|',
                ('max_amount', '>=', transfer.amount),
                ('max_amount', '=', 0),
            ], order='min_amount desc', limit=1)

            if threshold:
                transfer.required_approval_level = threshold.approval_level
            else:
                transfer.required_approval_level = 'manager'

    def _compute_attachment_count(self):
        for transfer in self:
            transfer.attachment_count = len(transfer.attachment_ids)

    def _compute_move_count(self):
        for transfer in self:
            count = 0
            if transfer.source_move_id:
                count += 1
            if transfer.destination_move_id:
                count += 1
            transfer.move_count = count

    # === ONCHANGE METHODS ===
    @api.onchange('source_journal_id')
    def _onchange_source_journal(self):
        """Set currency from source journal"""
        if self.source_journal_id:
            self.currency_id = (
                self.source_journal_id.currency_id or
                self.company_id.currency_id
            )

    @api.onchange('company_id')
    def _onchange_company(self):
        """Reset journals when company changes"""
        self.source_journal_id = False
        self.destination_journal_id = False
        self.transfer_account_id = False

    # === CONSTRAINT METHODS ===
    @api.constrains('source_journal_id', 'destination_journal_id')
    def _check_different_journals(self):
        for transfer in self:
            if transfer.source_journal_id and transfer.destination_journal_id:
                if transfer.source_journal_id == transfer.destination_journal_id:
                    raise ValidationError(_('Source and destination journals must be different!'))

    @api.constrains('amount')
    def _check_amount_positive(self):
        for transfer in self:
            if transfer.amount <= 0:
                raise ValidationError(_('Transfer amount must be positive!'))

    # === CRUD METHODS ===
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'internal.transfer'
                ) or _('New')
        return super().create(vals_list)

    def copy(self, default=None):
        default = dict(default or {})
        default['name'] = _('New')
        return super().copy(default)

    # === WORKFLOW ACTIONS ===
    def action_submit(self):
        """Submit transfer for approval"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Only draft transfers can be submitted.'))

        if not self.approver_id:
            raise UserError(_('Please select an approver before submitting.'))

        self.write({
            'state': 'submitted',
            'submitted_by_id': self.env.uid,
            'submit_date': fields.Datetime.now(),
        })

        # Create activity for the selected approver
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            user_id=self.approver_id.id,
            summary=_('Internal Transfer Approval Required'),
            note=_('Please review and approve internal transfer %s for %s %s from %s to %s.') % (
                self.name,
                '{:,.2f}'.format(self.amount),
                self.currency_id.name,
                self.source_journal_id.name,
                self.destination_journal_id.name,
            ),
        )

        self.message_post(
            body=_('Transfer submitted for approval to %s.') % self.approver_id.name,
            subtype_xmlid='mail.mt_note',
        )
        return True

    def action_approve(self):
        """Approve the transfer and auto-post journal entries"""
        self.ensure_one()
        if self.state != 'submitted':
            raise UserError(_('Only submitted transfers can be approved.'))

        # Check approval permissions
        self._check_approval_permission()

        # Create journal entries
        self._create_journal_entries()

        # Auto-reconcile
        self._auto_reconcile()

        self.write({
            'state': 'approved',
            'approved_by_id': self.env.uid,
            'approval_date': fields.Datetime.now(),
        })

        # Mark approval activity as done
        self.activity_feedback(['mail.mail_activity_data_todo'])

        self.message_post(
            body=_('Transfer approved by %s. Journal entries created and reconciled.') % self.env.user.name,
            subtype_xmlid='mail.mt_note',
        )
        return True

    def action_reject(self):
        """Open rejection wizard"""
        self.ensure_one()
        return {
            'name': _('Reject Transfer'),
            'type': 'ir.actions.act_window',
            'res_model': 'internal.transfer.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_transfer_id': self.id},
        }

    def action_cancel(self):
        """Open cancellation wizard"""
        self.ensure_one()
        if self.state == 'cancelled':
            raise UserError(_('This transfer is already cancelled.'))

        return {
            'name': _('Cancel Transfer'),
            'type': 'ir.actions.act_window',
            'res_model': 'internal.transfer.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_transfer_id': self.id},
        }

    def action_reset_to_draft(self):
        """Reset transfer to draft - for rejected, submitted or cancelled transfers"""
        self.ensure_one()
        if self.state == 'draft':
            raise UserError(_('This transfer is already in draft state.'))
        if self.state == 'approved':
            raise UserError(_('Approved transfers cannot be reset to draft. Use Cancel instead.'))

        # Clear relevant fields based on previous state
        vals = {
            'state': 'draft',
            'submitted_by_id': False,
            'submit_date': False,
        }
        if self.state == 'rejected':
            vals.update({
                'rejected_by_id': False,
                'rejection_reason': False,
                'rejection_date': False,
            })
        if self.state == 'cancelled':
            vals.update({
                'cancelled_by_id': False,
                'cancellation_reason': False,
                'cancellation_date': False,
            })

        # Cancel any pending activities
        self.activity_unlink(['mail.mail_activity_data_todo'])

        self.write(vals)
        self.message_post(
            body=_('Transfer reset to draft by %s.') % self.env.user.name,
            subtype_xmlid='mail.mt_note',
        )
        return True

    # === HELPER METHODS ===
    def _check_approval_permission(self):
        """Check if current user can approve based on required level"""
        self.ensure_one()
        user = self.env.user

        # Use standard Odoo accounting groups for permission checks
        # account.group_account_manager can approve all transfers
        if not user.has_group('account.group_account_manager'):
            raise UserError(_('You do not have permission to approve transfers. '
                             'Only Account Managers can approve internal transfers.'))

    def _get_journal_entry_narration(self):
        """Build comprehensive narration for journal entries"""
        self.ensure_one()
        lines = [
            _('Internal Transfer: %s') % self.name,
            _('From: %s (%s)') % (self.source_journal_id.name, self.source_account_id.code),
            _('To: %s (%s)') % (self.destination_journal_id.name, self.destination_account_id.code),
            _('Amount: %s %s') % ('{:,.2f}'.format(self.amount), self.currency_id.name),
            _('Date: %s') % self.date.strftime('%Y-%m-%d'),
        ]
        if self.memo:
            lines.append(_('Memo: %s') % self.memo)
        if self.approved_by_id:
            lines.append(_('Approved By: %s') % self.approved_by_id.name)
        return '\n'.join(lines)

    def _create_journal_entries(self):
        """Create paired journal entries for the transfer"""
        self.ensure_one()

        AccountMove = self.env['account.move']

        # Build comprehensive reference
        ref = self._get_journal_entry_narration()
        short_ref = _('Internal Transfer: %s') % self.name
        if self.memo:
            short_ref = '%s - %s' % (short_ref, self.memo)

        # Company currency for comparison
        company_currency = self.company_id.currency_id

        # === SOURCE JOURNAL ENTRY ===
        # Debit: Transfer Account, Credit: Source Bank/Cash Account
        source_move_vals = {
            'date': self.date,
            'ref': short_ref,
            'narration': ref,
            'journal_id': self.source_journal_id.id,
            'company_id': self.company_id.id,
            'line_ids': [
                (0, 0, {
                    'name': short_ref,
                    'account_id': self.transfer_account_id.id,
                    'debit': self.amount if self.currency_id == company_currency else 0.0,
                    'credit': 0.0,
                    'currency_id': self.currency_id.id if self.currency_id != company_currency else False,
                    'amount_currency': self.amount if self.currency_id != company_currency else 0.0,
                }),
                (0, 0, {
                    'name': short_ref,
                    'account_id': self.source_account_id.id,
                    'debit': 0.0,
                    'credit': self.amount if self.currency_id == company_currency else 0.0,
                    'currency_id': self.currency_id.id if self.currency_id != company_currency else False,
                    'amount_currency': -self.amount if self.currency_id != company_currency else 0.0,
                }),
            ],
        }
        source_move = AccountMove.create(source_move_vals)
        source_move.action_post()

        # === DESTINATION JOURNAL ENTRY ===
        # Debit: Destination Bank/Cash Account, Credit: Transfer Account
        dest_amount = self.destination_amount if self.is_multi_currency else self.amount
        dest_currency = self.destination_currency_id if self.is_multi_currency else self.currency_id

        destination_move_vals = {
            'date': self.date,
            'ref': short_ref,
            'narration': ref,
            'journal_id': self.destination_journal_id.id,
            'company_id': self.company_id.id,
            'line_ids': [
                (0, 0, {
                    'name': short_ref,
                    'account_id': self.destination_account_id.id,
                    'debit': dest_amount if dest_currency == company_currency else 0.0,
                    'credit': 0.0,
                    'currency_id': dest_currency.id if dest_currency != company_currency else False,
                    'amount_currency': dest_amount if dest_currency != company_currency else 0.0,
                }),
                (0, 0, {
                    'name': short_ref,
                    'account_id': self.transfer_account_id.id,
                    'debit': 0.0,
                    'credit': dest_amount if dest_currency == company_currency else 0.0,
                    'currency_id': dest_currency.id if dest_currency != company_currency else False,
                    'amount_currency': -dest_amount if dest_currency != company_currency else 0.0,
                }),
            ],
        }
        destination_move = AccountMove.create(destination_move_vals)
        destination_move.action_post()

        self.write({
            'source_move_id': source_move.id,
            'destination_move_id': destination_move.id,
        })

    def _auto_reconcile(self):
        """Auto-reconcile the transfer account entries"""
        self.ensure_one()

        if not self.source_move_id or not self.destination_move_id:
            return

        # Find the transfer account lines from both moves
        transfer_lines = self.env['account.move.line'].search([
            ('move_id', 'in', [self.source_move_id.id, self.destination_move_id.id]),
            ('account_id', '=', self.transfer_account_id.id),
            ('reconciled', '=', False),
        ])

        if len(transfer_lines) == 2:
            try:
                transfer_lines.reconcile()
            except Exception as e:
                # Log warning but don't fail the transfer
                self.message_post(
                    body=_('Auto-reconciliation warning: %s. Please reconcile manually.') % str(e),
                    subtype_xmlid='mail.mt_note',
                )

    def _create_reversal_entries(self, reason):
        """Create reversal journal entries for cancellation"""
        self.ensure_one()

        if not self.source_move_id or not self.destination_move_id:
            return

        # Reverse both moves
        for move in [self.source_move_id, self.destination_move_id]:
            reversal_wizard = self.env['account.move.reversal'].with_context(
                active_model='account.move',
                active_ids=move.ids,
            ).create({
                'reason': reason or _('Transfer Cancellation: %s') % self.name,
                'refund_method': 'cancel',
                'journal_id': move.journal_id.id,
            })
            reversal_wizard.refund_moves()

    # === ACTION METHODS FOR VIEWS ===
    def action_view_journal_entries(self):
        """Open related journal entries"""
        self.ensure_one()
        move_ids = []
        if self.source_move_id:
            move_ids.append(self.source_move_id.id)
        if self.destination_move_id:
            move_ids.append(self.destination_move_id.id)

        if len(move_ids) == 1:
            return {
                'name': _('Journal Entry'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': move_ids[0],
                'view_mode': 'form',
            }
        return {
            'name': _('Journal Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', move_ids)],
            'context': {'create': False},
        }

    def action_view_attachments(self):
        """Open attachments"""
        self.ensure_one()
        return {
            'name': _('Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [('id', 'in', self.attachment_ids.ids)],
            'context': {
                'default_res_model': 'internal.transfer',
                'default_res_id': self.id,
            },
        }
