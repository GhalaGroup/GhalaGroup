# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class JournalCustodian(models.Model):
    _name = 'journal.custodian'
    _description = 'Journal Custodian Assignment'
    _rec_name = 'journal_id'
    _order = 'journal_id'

    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        required=True,
        domain="[('type', 'in', ['bank', 'cash']), ('company_id', '=', company_id)]",
        help="Bank or Cash journal to assign custodians to",
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    custodian_ids = fields.Many2many(
        'res.users',
        'journal_custodian_user_rel',
        'custodian_id',
        'user_id',
        string='Primary Custodians',
        help="Users responsible for this bank/cash account. They can confirm receipt of funds.",
    )
    backup_ids = fields.Many2many(
        'res.users',
        'journal_custodian_backup_rel',
        'custodian_id',
        'user_id',
        string='Backup Managers',
        help="Senior managers who can confirm receipt when primary custodians are unavailable.",
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    notes = fields.Text(
        string='Notes',
        help="Internal notes about this custodian assignment",
    )

    _sql_constraints = [
        ('journal_company_uniq', 'unique(journal_id, company_id)',
         'A custodian assignment already exists for this journal in this company!'),
    ]

    @api.constrains('custodian_ids', 'backup_ids')
    def _check_custodians(self):
        """Ensure at least one custodian or backup is assigned"""
        for record in self:
            if not record.custodian_ids and not record.backup_ids:
                raise ValidationError(
                    _("You must assign at least one primary custodian or backup manager to journal '%s'.")
                    % record.journal_id.name
                )

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Clear journal when company changes"""
        if self.journal_id and self.journal_id.company_id != self.company_id:
            self.journal_id = False

    def name_get(self):
        """Display journal name with company"""
        result = []
        for record in self:
            name = record.journal_id.name
            if record.company_id and len(self.env.companies) > 1:
                name = f"{name} ({record.company_id.name})"
            result.append((record.id, name))
        return result

    @api.model
    def get_custodians_for_journal(self, journal_id, company_id=None):
        """
        Get all custodians (primary + backup) for a journal.
        Returns recordset of res.users
        """
        if not company_id:
            company_id = self.env.company.id

        custodian = self.search([
            ('journal_id', '=', journal_id),
            ('company_id', '=', company_id),
            ('active', '=', True),
        ], limit=1)

        if custodian:
            return custodian.custodian_ids | custodian.backup_ids
        return self.env['res.users']

    @api.model
    def get_primary_custodians_for_journal(self, journal_id, company_id=None):
        """Get only primary custodians for a journal"""
        if not company_id:
            company_id = self.env.company.id

        custodian = self.search([
            ('journal_id', '=', journal_id),
            ('company_id', '=', company_id),
            ('active', '=', True),
        ], limit=1)

        if custodian:
            return custodian.custodian_ids
        return self.env['res.users']

    @api.model
    def get_backup_custodians_for_journal(self, journal_id, company_id=None):
        """Get only backup managers for a journal"""
        if not company_id:
            company_id = self.env.company.id

        custodian = self.search([
            ('journal_id', '=', journal_id),
            ('company_id', '=', company_id),
            ('active', '=', True),
        ], limit=1)

        if custodian:
            return custodian.backup_ids
        return self.env['res.users']

    @api.model
    def has_custodian(self, journal_id, company_id=None):
        """Check if a journal has any custodian assigned"""
        if not company_id:
            company_id = self.env.company.id

        return bool(self.search_count([
            ('journal_id', '=', journal_id),
            ('company_id', '=', company_id),
            ('active', '=', True),
        ]))
