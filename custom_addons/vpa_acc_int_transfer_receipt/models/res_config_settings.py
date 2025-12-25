# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_receipt_confirmation = fields.Boolean(
        related='company_id.enable_receipt_confirmation',
        readonly=False,
        string='Enable Receipt Confirmation',
        help="When enabled, internal transfers require custodian confirmation before "
             "journal entries are created.",
    )
