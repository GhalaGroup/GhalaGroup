# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime


class MrpProductionEffectiveDate(models.Model):
    """Extends mrp.production to allow changing effective dates with automatic synchronization."""

    _inherit = "mrp.production"

    date_of_completion = fields.Datetime(
        string="Effective Date",
        default=False,
        help="Set a custom effective date before marking as done. Leave empty to use current date/time."
    )

    def wiz_open_mo(self):
        """Opens the wizard to change effective date after completion."""
        return {
            'name': 'Change Effective Date',
            'type': 'ir.actions.act_window',
            'res_model': 'change.effective.wizard.mo',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_production_id': self.id},
        }

    def button_mark_done(self):
        """
        Override the mark done button to add custom effective date functionality.
        This allows setting a specific effective date instead of using the current date/time.
        """
        res = super(MrpProductionEffectiveDate, self).button_mark_done()

        # If completion date is set, apply it after validation
        if self.date_of_completion:
            self._apply_effective_date(self.date_of_completion)

        return res

    def _apply_effective_date(self, selected_date):
        """Apply the effective date to all related records."""
        # Check if stock_valuation_layer table exists
        self.env.cr.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'stock_valuation_layer'
            )
        """)
        has_valuation_layer = self.env.cr.fetchone()[0]

        # Check if account_move table exists
        self.env.cr.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'account_move'
            )
        """)
        has_accounting = self.env.cr.fetchone()[0]

        # Update the date_finished field
        self.date_finished = selected_date

        # Update stock moves related to this MO (both consumption and finished product)
        for stock_move in self.move_raw_ids | self.move_finished_ids:
            if stock_move.state == 'done':
                stock_move.date = selected_date
                # Update move lines
                for move_line in stock_move.move_line_ids:
                    move_line.date = selected_date

        # Update stock valuation layers
        if has_valuation_layer:
            # Update valuation layers for raw materials consumed
            for move in self.move_raw_ids.filtered(lambda m: m.state == 'done'):
                self.env.cr.execute(
                    "UPDATE stock_valuation_layer SET create_date = %s WHERE stock_move_id = %s",
                    [selected_date, move.id]
                )
            # Update valuation layers for finished products
            for move in self.move_finished_ids.filtered(lambda m: m.state == 'done'):
                self.env.cr.execute(
                    "UPDATE stock_valuation_layer SET create_date = %s WHERE stock_move_id = %s",
                    [selected_date, move.id]
                )

        # Update account moves (journal entries)
        if has_accounting:
            account_move_ids = []
            move_ids = (self.move_raw_ids | self.move_finished_ids).filtered(lambda m: m.state == 'done').ids

            if move_ids:
                # Method 1: Try to get journal entries via valuation layers (if they exist)
                if has_valuation_layer:
                    self.env.cr.execute(
                        "SELECT DISTINCT account_move_id FROM stock_valuation_layer WHERE stock_move_id IN %s AND account_move_id IS NOT NULL",
                        [tuple(move_ids)]
                    )
                    account_move_ids = [row[0] for row in self.env.cr.fetchall()]

                # Method 2: If no valuation layer links, find journal entries by MO reference
                if not account_move_ids:
                    # Find journal entries with this MO's name in the reference
                    self.env.cr.execute(
                        "SELECT DISTINCT id FROM account_move WHERE ref LIKE %s AND state = 'posted'",
                        [f"{self.name} - %"]
                    )
                    account_move_ids = [row[0] for row in self.env.cr.fetchall()]

            if account_move_ids:
                selected_date_only = selected_date.date() if isinstance(selected_date, datetime) else selected_date

                # Update account move dates
                self.env.cr.execute(
                    "UPDATE account_move SET date = %s WHERE id IN %s",
                    [selected_date_only, tuple(account_move_ids)]
                )
                # Update account move line dates
                self.env.cr.execute(
                    "UPDATE account_move_line SET date = %s WHERE move_id IN %s",
                    [selected_date_only, tuple(account_move_ids)]
                )

                # Update journal entry names if date is in different month/year
                selected_datetime = selected_date if isinstance(selected_date, datetime) else datetime.combine(selected_date, datetime.min.time())
                selected_month = selected_datetime.month
                selected_year = selected_datetime.year
                current_month = datetime.now().month
                current_year = datetime.now().year

                if selected_month != current_month or selected_year != current_year:
                    self._update_journal_names(account_move_ids, selected_datetime)

    def _update_journal_names(self, account_move_ids, selected_date):
        """Update journal entry names with new sequence based on selected date."""
        selected_year = selected_date.strftime("%Y")
        selected_month = selected_date.strftime("%m")

        # Track sequence numbers per journal to handle multiple entries
        journal_sequences = {}

        for account_move in self.env['account.move'].browse(account_move_ids):
            if not account_move.journal_id.code:
                continue

            journal_id = account_move.journal_id.id
            selected_prefix = f"{account_move.journal_id.code}/{selected_year}/{selected_month}/"

            # Get or calculate the next sequence number for this journal
            if journal_id not in journal_sequences:
                # Find the max sequence number for this prefix (first time for this journal)
                existing_moves = self.env['account.move'].search([
                    ('sequence_prefix', '=', selected_prefix),
                    ('id', 'not in', account_move_ids),  # Exclude the ones we're updating
                ])
                seq_numbers = [m.sequence_number for m in existing_moves if m.sequence_number]
                journal_sequences[journal_id] = max(seq_numbers, default=0)

            # Increment and use the next sequence number
            journal_sequences[journal_id] += 1
            next_sequence = journal_sequences[journal_id]

            # Update the journal entry
            new_name = f"{selected_prefix}{str(next_sequence).zfill(4)}"
            self.env.cr.execute(
                "UPDATE account_move SET name = %s, sequence_number = %s, sequence_prefix = %s WHERE id = %s",
                [new_name, next_sequence, selected_prefix, account_move.id]
            )
