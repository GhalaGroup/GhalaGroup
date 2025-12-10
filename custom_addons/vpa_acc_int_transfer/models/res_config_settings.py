# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Software Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    internal_transfer_memo_template = fields.Char(
        related='company_id.internal_transfer_memo_template',
        readonly=False,
        string='Memo Template',
    )
