# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models
from odoo.exceptions import UserError


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

    commission_trueup = fields.Boolean(
        string='Commission True-up Bill',
        help='Marks an excess (true-up) bill generated from a commission year. '
             'Used to number true-up runs structurally — the ref text is '
             'translated and cannot be matched reliably.',
    )

    def _post(self, soft=True):
        # Posting a commission bill into a CLOSED year would silently move a
        # settled year's ledger — same doctrine as every other entry point.
        for bill in self.filtered(
                lambda m: m.commission_year_id and m.move_type == 'in_invoice'):
            if bill.commission_year_id.sudo().state == 'closed':
                raise UserError(_(
                    'Commission year %(year)s is closed. Reopen it before '
                    'posting bill %(bill)s into it.',
                    year=bill.commission_year_id.sudo().display_name,
                    bill=bill.display_name or bill.ref,
                ))
        posted = super()._post(soft=soft)
        # Late-posting catch-up, both directions, one sync per unique pair
        # (sudo: the poster may have no commission rights at all):
        # - a commission bill posted AFTER payments were applied to its year
        # - a PAYMENT posted after being year-linked/allocated (its move is
        #   type 'entry'; found via origin_payment_id)
        Allocation = self.env['vpa.commission.payment.allocation'].sudo()
        pairs = set()
        for bill in posted.filtered(
                lambda m: m.commission_year_id and m.move_type == 'in_invoice'):
            year = bill.commission_year_id.sudo()
            for payment in (year.payment_ids | year.allocation_ids.payment_id):
                pairs.add((payment, year))
        for move in posted:
            payment = move.origin_payment_id.sudo()
            if payment:
                years = (payment.commission_year_id
                         | payment.commission_allocation_ids.scheme_year_id)
                for year in years:
                    pairs.add((payment, year))
        for payment, year in pairs:
            Allocation._sync_payment_year_reconciliation(payment, year)
        return posted

    def write(self, vals):
        """Moving a bill between commission years (or detaching it) orphans
        the matches that were justified by the OLD year's applied payments:
        drop the partials against this bill explicitly (the old year's sync
        can no longer see the bill once it left bill_ids), then resync both
        years' payments."""
        resync = set()
        if 'commission_year_id' in vals:
            Allocation = self.env['vpa.commission.payment.allocation'].sudo()
            for move in self:
                if move.move_type != 'in_invoice':
                    continue
                old_year = move.commission_year_id.sudo()
                if not old_year or old_year.id == vals.get('commission_year_id'):
                    continue
                bill_pay_lines = move.sudo().line_ids.filtered(
                    lambda l: l.account_id.account_type == 'liability_payable')
                partials = (bill_pay_lines.matched_debit_ids
                            | bill_pay_lines.matched_credit_ids).filtered(
                    lambda p: p.debit_move_id.move_id.origin_payment_id
                    or p.credit_move_id.move_id.origin_payment_id)
                if partials:
                    partials.unlink()
                for payment in (old_year.payment_ids
                                | old_year.allocation_ids.payment_id):
                    resync.add((payment.sudo(), old_year))
        res = super().write(vals)
        if 'commission_year_id' in vals and resync is not None:
            Allocation = self.env['vpa.commission.payment.allocation'].sudo()
            for move in self:
                new_year = move.commission_year_id.sudo()
                if move.move_type == 'in_invoice' and new_year:
                    for payment in (new_year.payment_ids
                                    | new_year.allocation_ids.payment_id):
                        resync.add((payment.sudo(), new_year))
            for payment, year in resync:
                Allocation._sync_payment_year_reconciliation(payment, year)
        return res

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
