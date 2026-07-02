# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    nns_enabled = fields.Boolean(
        related='company_id.nns_enabled',
        readonly=False,
        string='Prevent Negative Stock',
    )

    nns_mode = fields.Selection(
        related='company_id.nns_mode',
        readonly=False,
        string='Mode',
    )

    nns_alert_user_ids = fields.Many2many(
        related='company_id.nns_alert_user_ids',
        readonly=False,
        string='Alert Users',
    )

    nns_adj_approval = fields.Boolean(
        related='company_id.nns_adj_approval',
        readonly=False,
        string='Require Approval for Inventory Adjustments',
    )

    nns_adj_approver_ids = fields.Many2many(
        related='company_id.nns_adj_approver_ids',
        readonly=False,
        string='Adjustment Approvers',
    )
