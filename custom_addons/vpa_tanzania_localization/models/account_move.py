# -*- coding: utf-8 -*-
# Part of VPA Tanzania Localization. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2025 VPA Software Limited

from odoo import models, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.constrains('journal_id', 'move_type')
    def _check_journal_move_type(self):
        """
        Ensure proper journal types are used for invoices/bills.
        Auto-corrects purchase document journals when possible.

        This prevents errors when creating vendor bills with incorrect journal types,
        which is common in multi-currency scenarios.
        """
        for move in self:
            # Check purchase documents (bills, refunds, receipts)
            if move.is_purchase_document(include_receipts=True):
                if move.journal_id.type != 'purchase':
                    # Try to find a suitable purchase journal
                    currency = move.invoice_line_ids[0].currency_id if move.invoice_line_ids else move.currency_id

                    purchase_journal = self.env['account.journal'].search([
                        ('type', '=', 'purchase'),
                        ('company_id', '=', move.company_id.id),
                        '|',
                        ('currency_id', '=', currency.id),
                        ('currency_id', '=', False),  # Default currency journals
                    ], limit=1)

                    if purchase_journal:
                        # Auto-correct: assign the correct purchase journal
                        move.journal_id = purchase_journal.id
                    else:
                        # No suitable journal found - raise error
                        raise ValidationError(_(
                            'Cannot create a purchase document in a non-purchase journal.\n\n'
                            'Please create a Purchase journal for currency: %s\n'
                            'Or select a purchase journal manually.'
                        ) % currency.name)

            # Check sale documents (invoices, credit notes, receipts)
            if move.is_sale_document(include_receipts=True):
                if move.journal_id.type != 'sale':
                    raise ValidationError(_(
                        'Cannot create a sales document in a non-sales journal.\n\n'
                        'Current journal: %s (Type: %s)\n'
                        'Please select a Sales journal.'
                    ) % (move.journal_id.name, move.journal_id.type))
