# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Software Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InternalTransferThreshold(models.Model):
    _name = 'internal.transfer.threshold'
    _description = 'Internal Transfer Approval Threshold'
    _order = 'min_amount'

    name = fields.Char(
        string='Name',
        required=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    min_amount = fields.Float(
        string='Minimum Amount',
        required=True,
        default=0.0,
        help='Minimum transfer amount for this threshold (inclusive)',
    )
    max_amount = fields.Float(
        string='Maximum Amount',
        help='Maximum transfer amount for this threshold. Leave 0 for unlimited.',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    approval_level = fields.Selection([
        ('manager', 'Manager'),
        ('admin', 'Administrator'),
    ], string='Required Approval Level', required=True, default='manager')
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('min_max_check', 'CHECK(max_amount = 0 OR max_amount >= min_amount)',
         'Maximum amount must be greater than or equal to minimum amount!'),
    ]

    @api.constrains('min_amount', 'max_amount', 'company_id', 'active')
    def _check_overlapping_thresholds(self):
        """Ensure thresholds don't overlap for the same company"""
        for threshold in self:
            if not threshold.active:
                continue

            domain = [
                ('company_id', '=', threshold.company_id.id),
                ('id', '!=', threshold.id),
                ('active', '=', True),
            ]
            overlapping = self.search(domain)
            for other in overlapping:
                # Check for overlap
                this_max = threshold.max_amount or float('inf')
                other_max = other.max_amount or float('inf')

                if not (threshold.min_amount > other_max or this_max < other.min_amount):
                    raise ValidationError(_(
                        'Threshold ranges cannot overlap! '
                        '"%s" overlaps with "%s".'
                    ) % (threshold.name, other.name))

    def name_get(self):
        result = []
        for record in self:
            if record.max_amount:
                name = '%s (%s - %s %s)' % (
                    record.name,
                    '{:,.2f}'.format(record.min_amount),
                    '{:,.2f}'.format(record.max_amount),
                    record.currency_id.name
                )
            else:
                name = '%s (%s+ %s)' % (
                    record.name,
                    '{:,.2f}'.format(record.min_amount),
                    record.currency_id.name
                )
            result.append((record.id, name))
        return result
