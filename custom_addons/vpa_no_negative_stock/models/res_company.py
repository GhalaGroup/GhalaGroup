# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    nns_enabled = fields.Boolean(
        string='Prevent Negative Stock',
        default=True,
        help='When enabled, stock operations that would drive on-hand quantity '
             'below zero are blocked (or warned, depending on the mode).',
    )

    nns_mode = fields.Selection(
        selection=[
            ('block', 'Hard Block'),
            ('warn', 'Soft Warn (Manager Override)'),
        ],
        string='Mode',
        default='block',
        help='Hard Block: the operation is stopped.\n'
             'Soft Warn (Manager Override): only an Inventory Manager can push '
             'the operation through, after entering a mandatory reason.',
    )

    nns_alert_user_ids = fields.Many2many(
        'res.users',
        'nns_company_alert_users_rel',
        'company_id',
        'user_id',
        string='Alert Users',
        help='Users who receive a to-do activity when a negative-stock block or '
             'override happens.',
    )

    # --- Inventory Adjustment Approval ---
    nns_adj_approval = fields.Boolean(
        string='Require Approval for Inventory Adjustments',
        default=False,
        help='When enabled, manual inventory adjustments (the Update Quantity / '
             'On-Hand count screen) require a reason and manager approval before '
             'the stock change is applied.',
    )

    nns_adj_approver_ids = fields.Many2many(
        'res.users',
        'nns_company_adj_approver_users_rel',
        'company_id',
        'user_id',
        string='Adjustment Approvers',
        help='Users who can approve or reject inventory adjustment requests. '
             'If empty, any Inventory Manager can approve.',
    )
