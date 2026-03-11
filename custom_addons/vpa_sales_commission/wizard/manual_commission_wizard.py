# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ManualCommissionWizard(models.TransientModel):
    _name = 'vpa.manual.commission.wizard'
    _description = 'Add Manual Commission'

    scheme_id = fields.Many2one(
        'vpa.commission.scheme',
        string='Commission Scheme',
        required=True,
        domain=[('active', '=', True)],
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        related='scheme_id.employee_id',
        readonly=True,
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Client',
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        domain="[('partner_id', '=', partner_id)]",
    )
    sale_order_ref = fields.Char(
        string='Customer Reference',
        related='sale_order_id.client_order_ref',
        readonly=True,
    )

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.sale_order_id = False
    base_amount = fields.Float(
        string='Base Amount',
        digits=(12, 2),
    )
    rate = fields.Float(
        string='Rate (%)',
        digits=(5, 2),
    )
    amount = fields.Float(
        string='Commission Amount',
        digits=(12, 2),
        required=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='scheme_id.currency_id',
        readonly=True,
    )
    notes = fields.Text(
        string='Reason / Note',
        required=True,
    )

    @api.onchange('base_amount', 'rate')
    def _onchange_calc_amount(self):
        if self.base_amount and self.rate:
            self.amount = self.base_amount * self.rate / 100

    def action_create(self):
        self.ensure_one()
        if self.amount <= 0:
            raise UserError(_('Commission amount must be greater than zero.'))
        line = self.env['vpa.commission.line'].create({
            'scheme_id': self.scheme_id.id,
            'type': 'manual',
            'date': self.date,
            'partner_id': self.partner_id.id if self.partner_id else False,
            'sale_order_name': self.sale_order_id.name if self.sale_order_id else False,
            'base_amount': self.base_amount,
            'rate': self.rate,
            'amount': self.amount,
            'notes': self.notes,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.commission.line',
            'view_mode': 'form',
            'res_id': line.id,
            'target': 'current',
        }
