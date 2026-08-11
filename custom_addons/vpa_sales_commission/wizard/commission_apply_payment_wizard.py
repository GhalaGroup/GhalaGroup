# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class VpaCommissionApplyPaymentWizard(models.TransientModel):
    """Apply an on-account payment (fully or partially) to a commission year."""
    _name = 'vpa.commission.apply.payment.wizard'
    _description = 'Apply On-Account Payment to Commission Year'

    scheme_year_id = fields.Many2one(
        'vpa.commission.scheme.year',
        string='Commission Year',
        required=True,
        readonly=True,
    )
    employee_id = fields.Many2one(related='scheme_year_id.employee_id')
    company_id = fields.Many2one(related='scheme_year_id.company_id')
    currency_id = fields.Many2one(related='scheme_year_id.currency_id')
    outstanding_cash = fields.Monetary(
        related='scheme_year_id.outstanding_cash',
        string='Outstanding for Year',
        currency_field='currency_id',
    )
    allowed_payment_ids = fields.Many2many(
        'account.payment',
        compute='_compute_allowed_payments',
    )
    payment_id = fields.Many2one(
        'account.payment',
        string='On-Account Payment',
        required=True,
        domain="[('id', 'in', allowed_payment_ids)]",
        help='Outbound payments not linked to any commission year and with an '
             'unallocated remainder. Payments to the employee are shown first; '
             'if none exist, all on-account payments of the company are listed.',
    )
    payment_partner_id = fields.Many2one(
        related='payment_id.partner_id', string='Paid To')
    # Explicit label: without it this inherits "Currency" from the related
    # field and collides with currency_id above, which Odoo warns about and
    # which makes the two indistinguishable in filters and exports.
    payment_currency_id = fields.Many2one(
        related='payment_id.currency_id', string='Payment Currency')
    payment_amount = fields.Monetary(
        related='payment_id.amount',
        string='Payment Total',
        currency_field='payment_currency_id',
    )
    unallocated_amount = fields.Monetary(
        related='payment_id.commission_unallocated_amount',
        string='Still Unallocated',
        currency_field='payment_currency_id',
    )
    amount_to_apply = fields.Monetary(
        string='Amount to Apply',
        currency_field='payment_currency_id',
        help='Portion of the payment (in the payment currency) to apply to '
             'this commission year. Defaults to the smaller of the payment\'s '
             'unallocated remainder and the year\'s outstanding balance.',
    )

    @api.depends('scheme_year_id')
    def _compute_allowed_payments(self):
        Payment = self.env['account.payment']
        for wiz in self:
            if not wiz.scheme_year_id:
                wiz.allowed_payment_ids = Payment
                continue
            base_domain = [
                ('payment_type', '=', 'outbound'),
                ('state', 'in', ('in_process', 'paid')),
                ('commission_year_id', '=', False),
                ('commission_unallocated_amount', '>', 0),
                ('company_id', '=', wiz.scheme_year_id.company_id.id),
            ]
            # Prefer payments made to the employee; fall back to all
            # on-account payments if none match (e.g. paid to another party).
            partner = wiz.scheme_year_id.employee_id.work_contact_id
            payments = Payment
            if partner:
                payments = Payment.search(
                    base_domain + [('partner_id', '=', partner.id)])
            if not payments:
                payments = Payment.search(base_domain)
            wiz.allowed_payment_ids = payments

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # Guard on active_model: active_ids may belong to another model
        # (the client injects them from whatever view launched the action).
        if (not res.get('scheme_year_id')
                and self.env.context.get('active_model') == 'vpa.commission.scheme.year'
                and self.env.context.get('active_id')):
            res['scheme_year_id'] = self.env.context['active_id']
        return res

    @api.onchange('payment_id')
    def _onchange_payment_id(self):
        for wiz in self:
            if not wiz.payment_id:
                wiz.amount_to_apply = 0.0
                continue
            unallocated = wiz.payment_id.commission_unallocated_amount
            outstanding = wiz.scheme_year_id.outstanding_cash
            if outstanding > 0:
                # Outstanding is in the scheme currency; convert to the
                # payment currency at the payment date for comparison.
                if (wiz.payment_currency_id and wiz.currency_id
                        and wiz.payment_currency_id != wiz.currency_id):
                    outstanding = wiz.currency_id._convert(
                        outstanding, wiz.payment_currency_id,
                        wiz.company_id or self.env.company,
                        wiz.payment_id.date or fields.Date.today(),
                    )
                wiz.amount_to_apply = min(unallocated, outstanding)
            else:
                wiz.amount_to_apply = unallocated

    def action_apply(self):
        self.ensure_one()
        currency = self.payment_currency_id
        if currency.compare_amounts(self.amount_to_apply, 0.0) <= 0:
            raise UserError(_('The amount to apply must be positive.'))
        if currency.compare_amounts(
                self.amount_to_apply,
                self.payment_id.commission_unallocated_amount) > 0:
            raise UserError(_(
                'You cannot apply %(amount)s: only %(rest)s of this payment '
                'is still unallocated.',
                amount=f'{self.amount_to_apply:,.2f} {currency.name}',
                rest=f'{self.payment_id.commission_unallocated_amount:,.2f} '
                     f'{currency.name}',
            ))
        self.env['vpa.commission.payment.allocation'].create({
            'payment_id': self.payment_id.id,
            'scheme_year_id': self.scheme_year_id.id,
            'amount': self.amount_to_apply,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': _('Payment Applied'),
                'message': _(
                    '%(amount)s from %(payment)s applied to %(year)s.',
                    amount=f'{self.amount_to_apply:,.2f} {currency.name}',
                    payment=self.payment_id.display_name,
                    year=self.scheme_year_id.display_name,
                ),
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
            },
        }
