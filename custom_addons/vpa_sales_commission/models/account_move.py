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
    commission_offset_amount = fields.Float(
        string='Guarantee Offset Applied',
        digits=(12, 2),
        help='Portion of the minimum guarantee advance deducted on this excess/true-up '
             'bill. Used to track how much of the guarantee coverage has been consumed.',
    )

    commission_writeoff = fields.Boolean(
        string='Commission Write-off',
        help='Marks a rounding write-off entry created by the commission pay wizard.',
    )

    def unlink(self):
        # Deleting a commission bill (guarantee or true-up) must also remove its
        # monthly spread entries — otherwise they survive as orphan expense and
        # double-count when the bill is regenerated.
        deferred = self.filtered(
            lambda m: m.commission_year_id and m.move_type == 'in_invoice'
        ).deferred_move_ids
        res = super().unlink()
        if deferred:
            deferred.filtered(lambda m: m.state == 'posted').button_draft()
            deferred.unlink()
        return res
