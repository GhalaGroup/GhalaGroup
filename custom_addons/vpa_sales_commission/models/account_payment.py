# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    commission_year_id = fields.Many2one(
        'vpa.commission.scheme.year',
        string='Commission Year',
        index=True,
        copy=False,
        help='Links this payment to an employee commission year. '
             'Set it when paying commission for a specific year, or leave empty '
             'for a payment on account and link it to a year later.',
    )
