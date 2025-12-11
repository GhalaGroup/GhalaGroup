# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Software Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    internal_transfer_memo_template = fields.Char(
        string='Memo Template',
        default='Internal Transfer from {source} to {destination} by {user}',
        help='Template for auto-generated memo. Use {source}, {destination}, {user}, {amount}, {date} as placeholders.',
    )

    # Transfer Permission Settings
    transfer_manager_ids = fields.Many2many(
        'res.users',
        'company_transfer_managers_rel',
        'company_id',
        'user_id',
        string='Transfer Managers',
        help='Users with full transfer control: approve, reject, cancel, reset, lock, unlock',
    )

    transfer_approver_ids = fields.Many2many(
        'res.users',
        'company_transfer_approvers_rel',
        'company_id',
        'user_id',
        string='Transfer Approvers',
        help='Users who can approve and reject internal transfers',
    )

    transfer_canceller_ids = fields.Many2many(
        'res.users',
        'company_transfer_cancellers_rel',
        'company_id',
        'user_id',
        string='Transfer Cancellers',
        help='Users who can cancel and reset transfers to draft',
    )
