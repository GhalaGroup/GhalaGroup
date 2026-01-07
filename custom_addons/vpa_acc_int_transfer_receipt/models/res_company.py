# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_receipt_confirmation = fields.Boolean(
        string='Enable Receipt Confirmation',
        default=False,
        help="When enabled, internal transfers require custodian confirmation before "
             "journal entries are created. Custodians must confirm they received the funds.",
    )
