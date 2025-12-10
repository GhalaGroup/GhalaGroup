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
