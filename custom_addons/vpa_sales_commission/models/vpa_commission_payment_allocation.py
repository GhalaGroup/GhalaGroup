# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class VpaCommissionPaymentAllocation(models.Model):
    """Split of a payment on account across commission years.

    A payment made without a Commission Year link ("payment on account")
    can later be applied — fully or partially — to one or more commission
    years through these allocation lines. The unallocated remainder stays
    on account until it is applied.
    """
    _name = 'vpa.commission.payment.allocation'
    _description = 'Commission Payment Allocation'
    _order = 'payment_id desc, id'

    payment_id = fields.Many2one(
        'account.payment',
        string='Payment',
        required=True,
        ondelete='cascade',
        index=True,
        domain=[('payment_type', '=', 'outbound')],
    )
    scheme_year_id = fields.Many2one(
        'vpa.commission.scheme.year',
        string='Commission Year',
        required=True,
        ondelete='restrict',
        index=True,
    )
    amount = fields.Monetary(
        string='Allocated Amount',
        currency_field='currency_id',
        required=True,
        help='Portion of the payment (in the payment currency) applied to '
             'this commission year.',
    )
    currency_id = fields.Many2one(related='payment_id.currency_id')
    company_id = fields.Many2one(
        related='payment_id.company_id', store=True, index=True)
    employee_id = fields.Many2one(related='scheme_year_id.employee_id')
    payment_date = fields.Date(related='payment_id.date', string='Payment Date')
    payment_state = fields.Selection(related='payment_id.state', string='Payment Status')

    @api.constrains('amount', 'payment_id', 'scheme_year_id')
    def _check_allocation(self):
        for alloc in self:
            payment = alloc.payment_id
            currency = payment.currency_id
            if alloc.scheme_year_id.state == 'closed':
                # A closed year is reconciled: money landing in it afterwards
                # would silently move settled totals (same doctrine as the
                # closed-year guard on commission lines).
                raise ValidationError(_(
                    'Commission year %(year)s is closed. Reopen it before '
                    'applying payments to it.',
                    year=alloc.scheme_year_id.display_name,
                ))
            if currency.compare_amounts(alloc.amount, 0.0) <= 0:
                raise ValidationError(_(
                    'The allocated amount must be positive.'))
            if payment.payment_type != 'outbound':
                raise ValidationError(_(
                    'Only outbound (vendor) payments can be allocated to '
                    'commission years.'))
            if payment.commission_year_id:
                raise ValidationError(_(
                    'Payment %(payment)s is already fully linked to commission '
                    'year %(year)s. Remove the Commission Year link on the '
                    'payment before splitting it with allocations.',
                    payment=payment.display_name,
                    year=payment.commission_year_id.display_name,
                ))
            if (alloc.scheme_year_id.company_id and payment.company_id
                    and alloc.scheme_year_id.company_id != payment.company_id):
                raise ValidationError(_(
                    'The payment and the commission year belong to different '
                    'companies.'))
            total = sum(payment.commission_allocation_ids.mapped('amount'))
            if currency.compare_amounts(total, payment.amount) > 0:
                raise ValidationError(_(
                    'Total allocations (%(total)s) exceed the payment amount '
                    '(%(amount)s). Unallocated remainder cannot be negative.',
                    total=f'{total:,.2f} {currency.name}',
                    amount=f'{payment.amount:,.2f} {currency.name}',
                ))

    # ---- Chatter audit on the commission year ----
    @api.model_create_multi
    def create(self, vals_list):
        allocations = super().create(vals_list)
        for alloc in allocations:
            alloc.scheme_year_id.message_post(body=_(
                'Payment allocation added: %(amount)s from payment %(payment)s '
                '(unallocated remainder: %(rest)s).',
                amount=f'{alloc.amount:,.2f} {alloc.currency_id.name}',
                payment=alloc.payment_id.display_name,
                rest=f'{alloc.payment_id.commission_unallocated_amount:,.2f} '
                     f'{alloc.currency_id.name}',
            ))
        return allocations

    def unlink(self):
        for alloc in self:
            if alloc.scheme_year_id.state == 'closed':
                raise ValidationError(_(
                    'Commission year %(year)s is closed. Reopen it before '
                    'removing payment allocations from it.',
                    year=alloc.scheme_year_id.display_name,
                ))
            alloc.scheme_year_id.message_post(body=_(
                'Payment allocation removed: %(amount)s from payment %(payment)s.',
                amount=f'{alloc.amount:,.2f} {alloc.currency_id.name}',
                payment=alloc.payment_id.display_name,
            ))
        return super().unlink()
