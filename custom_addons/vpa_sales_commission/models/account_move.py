# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    commission_year_id = fields.Many2one(
        'vpa.commission.scheme.year',
        string='Commission Year',
        ondelete='set null',
        index=True,
        help='The commission scheme year this bill belongs to',
    )
    commission_month = fields.Char(
        string='Commission Month',
        help='Month (MM) this bill covers, for monthly commission bills',
    )
    commission_line_ids = fields.One2many(
        'vpa.commission.line',
        'bill_id',
        string='Commission Lines',
    )
