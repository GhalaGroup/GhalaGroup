# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    internal_transfer_memo_template = fields.Char(
        related='company_id.internal_transfer_memo_template',
        readonly=False,
        string='Memo Template',
    )

    # Transfer Permission Settings
    transfer_manager_ids = fields.Many2many(
        related='company_id.transfer_manager_ids',
        readonly=False,
        string='Transfer Managers',
    )

    transfer_approver_ids = fields.Many2many(
        related='company_id.transfer_approver_ids',
        readonly=False,
        string='Transfer Approvers',
    )

    transfer_canceller_ids = fields.Many2many(
        related='company_id.transfer_canceller_ids',
        readonly=False,
        string='Transfer Cancellers',
    )
