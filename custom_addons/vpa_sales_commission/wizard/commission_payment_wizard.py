# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CommissionPaymentWizard(models.TransientModel):
    _name = 'vpa.commission.payment.wizard'
    _description = 'Commission Payment Wizard'

    payment_method = fields.Selection([
        ('existing', 'Link Existing Payment'),
        ('new', 'Create New Payment'),
    ], string='Payment Method', default='existing', required=True)

    line_ids = fields.Many2many(
        'vpa.commission.line',
        'vpa_commission_payment_wizard_line_rel',
        'wizard_id',
        'line_id',
        string='Commission Lines',
    )

    total_amount = fields.Float(
        string='Total Amount',
        digits=(12, 2),
        compute='_compute_total_amount',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        compute='_compute_currency',
    )

    # For linking existing payment
    existing_payment_id = fields.Many2one(
        'account.payment',
        string='Existing Payment',
        domain="[('payment_type', '=', 'outbound'), ('state', 'in', ('paid', 'in_process'))]",
    )

    # For creating new payment
    journal_id = fields.Many2one(
        'account.journal',
        string='Payment Journal',
        domain="[('type', 'in', ('bank', 'cash'))]",
    )
    payment_date = fields.Date(
        string='Payment Date',
        default=fields.Date.today,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        compute='_compute_partner',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            lines = self.env['vpa.commission.line'].browse(active_ids)
            # Only include confirmed lines (not pending, paid, or cancelled)
            payable_lines = lines.filtered(lambda l: l.state == 'confirmed')
            if not payable_lines:
                raise UserError(_('No confirmed commission lines selected. Only confirmed lines can be paid.'))
            # Check all lines belong to same employee/scheme
            schemes = payable_lines.mapped('scheme_id')
            if len(schemes) > 1:
                raise UserError(_('All selected commission lines must belong to the same employee/scheme.'))
            res['line_ids'] = [(6, 0, payable_lines.ids)]
        return res

    @api.depends('line_ids', 'line_ids.amount')
    def _compute_total_amount(self):
        for wizard in self:
            wizard.total_amount = sum(wizard.line_ids.mapped('amount'))

    @api.depends('line_ids')
    def _compute_currency(self):
        for wizard in self:
            if wizard.line_ids:
                wizard.currency_id = wizard.line_ids[0].currency_id
            else:
                wizard.currency_id = self.env.company.currency_id

    @api.depends('line_ids')
    def _compute_partner(self):
        for wizard in self:
            if wizard.line_ids and wizard.line_ids[0].employee_id:
                employee = wizard.line_ids[0].employee_id
                wizard.partner_id = employee.work_contact_id or False
            else:
                wizard.partner_id = False

    def action_make_payment(self):
        """Process the payment - either link existing or create new."""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('No commission lines selected.'))

        if self.payment_method == 'existing':
            return self._link_existing_payment()
        else:
            return self._create_new_payment()

    def _link_existing_payment(self):
        """Link an existing accounting payment to the commission lines."""
        if not self.existing_payment_id:
            raise UserError(_('Please select an existing payment to link.'))

        payment = self.existing_payment_id
        self.line_ids.write({
            'state': 'paid',
            'paid_date': payment.date,
            'paid_by': self.env.uid,
            'payment_id': payment.id,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Payment Linked'),
                'message': _('%d commission line(s) marked as paid.', len(self.line_ids)),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def _create_new_payment(self):
        """Create a new outgoing payment and link it to the commission lines."""
        if not self.journal_id:
            raise UserError(_('Please select a payment journal.'))
        if not self.payment_date:
            raise UserError(_('Please set a payment date.'))

        employee = self.line_ids[0].employee_id
        partner = employee.work_contact_id
        if not partner:
            raise UserError(_(
                'Employee "%s" has no work contact (partner) set. '
                'Please configure the work contact on the employee form first.',
                employee.name,
            ))

        payment_vals = {
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'partner_id': partner.id,
            'amount': self.total_amount,
            'currency_id': self.currency_id.id,
            'journal_id': self.journal_id.id,
            'date': self.payment_date,
            'memo': _('Commission payment - %s', employee.name),
        }
        payment = self.env['account.payment'].create(payment_vals)

        self.line_ids.write({
            'state': 'paid',
            'paid_date': self.payment_date,
            'paid_by': self.env.uid,
            'payment_id': payment.id,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Payment Created'),
                'message': _('Payment of %s %s created and %d commission line(s) marked as paid.',
                             self.currency_id.symbol, self.total_amount, len(self.line_ids)),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
