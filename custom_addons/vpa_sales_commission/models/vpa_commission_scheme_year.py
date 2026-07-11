# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class VpaCommissionSchemeYear(models.Model):
    _name = 'vpa.commission.scheme.year'
    _description = 'Commission Scheme Year'
    _inherit = ['mail.thread']
    _order = 'year desc'
    _rec_name = 'display_name'

    scheme_id = fields.Many2one(
        'vpa.commission.scheme',
        string='Commission Scheme',
        required=True,
        ondelete='cascade',
        index=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        related='scheme_id.employee_id',
        store=True,
        index=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='scheme_id.company_id',
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='scheme_id.currency_id',
        store=True,
    )

    @api.model
    def _get_year_selection(self):
        current_year = fields.Date.today().year
        return [(str(y), str(y)) for y in range(2020, current_year + 3)]

    year = fields.Selection(
        selection='_get_year_selection',
        string='Year',
        required=True,
        index=True,
    )
    display_name = fields.Char(
        string='Name',
        compute='_compute_display_name',
        store=True,
    )
    production_rate = fields.Float(
        string='Rate (%)',
        digits=(5, 2),
        help='Commission percentage for this year. Leave 0 to use the scheme default rate.',
    )
    effective_rate = fields.Float(
        string='Effective Rate (%)',
        digits=(5, 2),
        compute='_compute_effective_rate',
        help='The rate actually applied: this year\'s rate if set, otherwise the scheme default.',
    )

    @api.depends('production_rate', 'scheme_id.production_rate')
    def _compute_effective_rate(self):
        for rec in self:
            rec.effective_rate = rec.production_rate or rec.scheme_id.production_rate
    minimum_amount = fields.Monetary(
        string='Min. Guarantee',
        currency_field='currency_id',
        help='Annual minimum commission guarantee for this year',
    )
    minimum_amount_usd = fields.Float(
        string='USD Equivalent',
        digits=(12, 2),
        help='USD equivalent of the minimum guarantee. Type here to fill the '
             'scheme-currency amount, or type the scheme amount to back-fill this. '
             'Converted using the rate at Dec 31 of the year (capped at today).',
    )

    def _get_usd_rate_date(self):
        """Dec 31 of the selected year, capped at today for current/future years."""
        import datetime
        rate_date = datetime.date(int(self.year), 12, 31)
        today = fields.Date.today()
        return min(rate_date, today)

    @api.onchange('minimum_amount_usd', 'year')
    def _onchange_minimum_amount_usd(self):
        """USD entered -> fill the scheme-currency Min. Guarantee."""
        # Skip when this onchange was itself triggered by the reverse fill.
        if self.env.context.get('_skip_min_guarantee_sync'):
            return
        if not self.minimum_amount_usd or not self.year:
            return
        usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if not usd or not self.currency_id or self.currency_id == usd:
            return
        converted = usd._convert(
            self.minimum_amount_usd,
            self.currency_id,
            self.company_id or self.env.company,
            self._get_usd_rate_date(),
        )
        self.with_context(_skip_min_guarantee_sync=True).minimum_amount = converted

    @api.onchange('minimum_amount', 'year')
    def _onchange_minimum_amount(self):
        """Scheme-currency Min. Guarantee entered -> back-fill the USD equivalent."""
        # Skip when this onchange was itself triggered by the USD fill.
        if self.env.context.get('_skip_min_guarantee_sync'):
            return
        if not self.minimum_amount or not self.year:
            return
        usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if not usd or not self.currency_id:
            return
        if self.currency_id == usd:
            self.with_context(_skip_min_guarantee_sync=True).minimum_amount_usd = self.minimum_amount
            return
        converted = self.currency_id._convert(
            self.minimum_amount,
            usd,
            self.company_id or self.env.company,
            self._get_usd_rate_date(),
        )
        self.with_context(_skip_min_guarantee_sync=True).minimum_amount_usd = converted
    expense_account_id = fields.Many2one(
        'account.account',
        string='Expense Account',
        domain="[('account_type', 'in', ('expense', 'expense_direct_cost'))]",
        help='Debit account for commission expense journal entries. Overrides scheme default.',
    )
    effective_expense_account_id = fields.Many2one(
        'account.account',
        string='Effective Expense Account',
        compute='_compute_effective_expense_account',
        help='The account this year will actually bill to: the year override if set, '
             'otherwise the scheme default expense account.',
    )

    @api.depends('expense_account_id', 'scheme_id.expense_account_id')
    def _compute_effective_expense_account(self):
        for rec in self:
            rec.effective_expense_account_id = (
                rec.expense_account_id or rec.scheme_id.expense_account_id
            )

    notes = fields.Text(string='Notes')

    # Year state
    state = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed'),
    ], string='State', default='open', required=True)

    # Computed totals from commission lines
    total_earned = fields.Monetary(
        string='Total Earned',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
    )
    total_paid = fields.Monetary(
        string='Total Paid',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
    )
    total_pending = fields.Monetary(
        string='Pending',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
    )
    shortfall = fields.Monetary(
        string='Shortfall',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
        help='How much below the minimum guarantee',
    )
    outstanding = fields.Monetary(
        string='Outstanding (Earned)',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
        help='Earned but not yet paid',
    )

    # Bills
    bill_ids = fields.One2many(
        'account.move',
        'commission_year_id',
        string='Vendor Bills',
        domain=[('move_type', '=', 'in_invoice')],
    )
    bill_count = fields.Integer(
        string='Bills',
        compute='_compute_bill_count',
    )
    mo_count = fields.Integer(
        string='Manufacturing Orders',
        compute='_compute_mo_so_counts',
    )
    so_count = fields.Integer(
        string='Sales Orders',
        compute='_compute_mo_so_counts',
    )
    line_count = fields.Integer(
        string='Commission Lines',
        compute='_compute_mo_so_counts',
    )

    def _year_commission_lines(self):
        """Non-cancelled commission lines for this scheme + year."""
        self.ensure_one()
        return self.scheme_id.commission_line_ids.filtered(
            lambda l: l.date_year == self.year and l.state != 'cancelled'
        )

    @api.depends('scheme_id.commission_line_ids', 'scheme_id.commission_line_ids.date_year',
                 'scheme_id.commission_line_ids.state')
    def _compute_mo_so_counts(self):
        for rec in self:
            lines = rec._year_commission_lines()
            rec.line_count = len(lines)
            rec.mo_count = len(lines.mapped('production_id'))
            rec.so_count = len({n for n in lines.mapped('sale_order_name') if n})

    # Advance tracking: guarantee coverage consumed by the true-up bill offsets
    advance_consumed = fields.Monetary(
        string='Advance Consumed',
        currency_field='currency_id',
        compute='_compute_advance',
        store=True,
        help='Guarantee coverage already applied as offsets on excess (true-up) bills.',
    )
    advance_remaining = fields.Monetary(
        string='Advance Remaining',
        currency_field='currency_id',
        compute='_compute_advance',
        store=True,
        help='Guarantee coverage not yet applied on excess (true-up) bills.',
    )
    payable_to_employee = fields.Monetary(
        string='Earned Above Guarantee',
        currency_field='currency_id',
        compute='_compute_advance',
        store=True,
        help='Confirmed commission above the minimum guarantee — what the employee '
             'is owed beyond the advance.',
    )

    # Cash payments (year-linked payments + payments matched to this year's bills)
    payment_ids = fields.One2many(
        'account.payment',
        'commission_year_id',
        string='Linked Payments',
    )
    payment_count = fields.Integer(
        string='Payments',
        compute='_compute_cash_payments',
    )
    amount_due_year = fields.Monetary(
        string='Due for Year',
        currency_field='currency_id',
        compute='_compute_cash_payments',
        help='What the employee is entitled to for this year: the greater of '
             'CONFIRMED commission and the minimum guarantee. Pending lines do '
             'not count until they are approved.',
    )
    amount_paid_cash = fields.Monetary(
        string='Paid',
        currency_field='currency_id',
        compute='_compute_cash_payments',
        help='Actual cash paid: payments linked to this year plus payments '
             'matched against this year\'s bills.',
    )
    outstanding_cash = fields.Monetary(
        string='Outstanding',
        currency_field='currency_id',
        compute='_compute_cash_payments',
        help='Due for the year minus cash paid and rounding write-offs. '
             'Negative means overpaid.',
    )
    writeoff_total = fields.Monetary(
        string='Written Off',
        currency_field='currency_id',
        compute='_compute_cash_payments',
        help='Rounding differences written off via the pay wizard.',
    )

    # Confirmation & excess (true-up) tracking
    confirmed_earned = fields.Monetary(
        string='Confirmed Earned',
        currency_field='currency_id',
        compute='_compute_excess',
        help='Sum of confirmed and paid commission lines for this year. '
             'Only confirmed commission can be billed and paid.',
    )
    pending_count = fields.Integer(
        string='Awaiting Confirmation',
        compute='_compute_excess',
    )
    excess_to_bill = fields.Monetary(
        string='Excess to Bill',
        currency_field='currency_id',
        compute='_compute_excess',
        help='Confirmed, unbilled commission above the remaining minimum-guarantee '
             'coverage. Generate the true-up bill to recognise this expense and payable.',
    )

    @api.depends(
        'scheme_id.commission_line_ids.state', 'scheme_id.commission_line_ids.amount',
        'scheme_id.commission_line_ids.date_year', 'scheme_id.commission_line_ids.bill_id',
        'minimum_amount', 'bill_ids.commission_offset_amount',
    )
    def _compute_excess(self):
        for rec in self:
            lines = rec._year_commission_lines()
            confirmed = lines.filtered(lambda l: l.state in ('confirmed', 'paid'))
            rec.confirmed_earned = sum(confirmed.mapped('amount'))
            rec.pending_count = len(lines.filtered(lambda l: l.state == 'pending'))
            confirmed_unbilled = sum(
                confirmed.filtered(lambda l: not l.bill_id).mapped('amount'))
            offsets_used = sum(rec.bill_ids.mapped('commission_offset_amount'))
            coverage_remaining = max(0.0, rec.minimum_amount - offsets_used)
            rec.excess_to_bill = max(0.0, confirmed_unbilled - coverage_remaining)

    def action_view_pending_lines(self):
        """Open the year's NOT-confirmed lines in the list (with the Confirm button)."""
        self.ensure_one()
        return {
            'name': _('To Approve - %s (%s)', self.employee_id.name, self.year),
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.commission.line',
            'view_mode': 'list,form',
            'domain': [
                ('scheme_id', '=', self.scheme_id.id),
                ('date_year', '=', self.year),
                ('state', '=', 'pending'),
            ],
        }

    def action_view_confirmed_lines(self):
        """Open the year's confirmed (and paid) lines in the list."""
        self.ensure_one()
        return {
            'name': _('Confirmed - %s (%s)', self.employee_id.name, self.year),
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.commission.line',
            'view_mode': 'list,form',
            'domain': [
                ('scheme_id', '=', self.scheme_id.id),
                ('date_year', '=', self.year),
                ('state', 'in', ('confirmed', 'paid')),
            ],
        }

    def action_confirm_all_lines(self):
        """Confirm every pending commission line of this year."""
        self.ensure_one()
        pending = self._year_commission_lines().filtered(lambda l: l.state == 'pending')
        return pending.action_bulk_confirm()

    def action_generate_excess_bill(self):
        """Bill the confirmed commission above the guarantee coverage (true-up).

        The bill itemises every confirmed unbilled line at full amount and adds one
        explicit negative line for the guarantee coverage still available, so the
        total equals exactly the excess payable. Expense is recognised at bill date.
        """
        self.ensure_one()
        if self.excess_to_bill <= 0:
            raise UserError(_(
                'Nothing to bill: confirmed unbilled commission does not exceed the '
                'remaining minimum-guarantee coverage. Confirm commission lines first.'))

        partner = self.employee_id.work_contact_id
        if not partner:
            raise UserError(_(
                'Employee "%s" has no work contact set.', self.employee_id.name))
        expense_account = self.scheme_id._get_expense_account_for_year(self.year)
        if not expense_account:
            raise UserError(_(
                'No expense account configured on the scheme or this year.'))
        journal = self.env['account.journal'].search([
            ('type', '=', 'purchase'),
            ('company_id', '=', self.company_id.id),
            ('currency_id', 'in', (self.currency_id.id, False)),
        ], limit=1)
        if not journal:
            raise UserError(_('No purchase journal found for %s.', self.company_id.name))

        lines = self._year_commission_lines().filtered(
            lambda l: l.state in ('confirmed', 'paid') and not l.bill_id)
        offsets_used = sum(self.bill_ids.mapped('commission_offset_amount'))
        coverage = max(0.0, self.minimum_amount - offsets_used)
        offset = min(coverage, sum(lines.mapped('amount')))

        # When prepaid accounting is configured, the bill books to the PREPAID
        # account and the expense is recognised per COMMISSION MONTH via journal
        # entries (Dr expense / Cr prepaid) — the excess hits the months the
        # commission was actually generated. Without prepaid config the expense
        # posts directly at bill date.
        company = self.company_id
        spread = bool(company.deferred_expense_account_id
                      and company.deferred_expense_journal_id)
        line_account = company.deferred_expense_account_id if spread else expense_account

        invoice_lines = []
        for cl in lines:
            mo_ref = cl.production_id.name if cl.production_id else cl.name
            name = f"{mo_ref} | {cl.item_name} | {cl.date}" if cl.item_name else f"{mo_ref} - {cl.date}"
            invoice_lines.append((0, 0, {
                'name': name,
                'quantity': 1.0,
                'price_unit': cl.amount,
                'account_id': line_account.id,
            }))
        if offset > 0:
            invoice_lines.append((0, 0, {
                'name': _('Less: covered by %s Minimum Guarantee advance', self.year),
                'quantity': 1.0,
                'price_unit': -offset,
                'account_id': line_account.id,
            }))

        # Date the true-up in the commission year (Dec 31) so the payable lands
        # in the right fiscal year; cap at today for the current year. The bill
        # is a draft — the date can still be adjusted before posting.
        import datetime
        year_end = datetime.date(int(self.year), 12, 31)
        invoice_date = min(fields.Date.context_today(self), year_end)
        bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': partner.id,
            'journal_id': journal.id,
            'invoice_date': invoice_date,
            'ref': _('Commission True-up - %s %s', self.employee_id.name, self.year),
            'invoice_line_ids': invoice_lines,
            'commission_year_id': self.id,
            'commission_offset_amount': offset,
        })
        lines.write({'bill_id': bill.id})

        if spread:
            self._create_excess_monthly_entries(
                bill, lines, coverage, expense_account,
                company.deferred_expense_account_id,
                company.deferred_expense_journal_id,
            )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Commission True-up Bill'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': bill.id,
            'target': 'current',
        }

    def _create_excess_monthly_entries(self, bill, lines, coverage, expense_account,
                                       prepaid_account, prepaid_journal):
        """Recognise the excess expense in the months the commission was generated.

        The guarantee coverage consumes the commission lines chronologically;
        whatever exceeds it is expensed in that line's month (Dr expense /
        Cr prepaid at month end).
        """
        import calendar
        import datetime

        remaining = coverage
        monthly = {}  # 'YYYY-MM' -> excess amount
        for cl in lines.sorted(key=lambda l: (l.date, l.id)):
            covered = min(remaining, cl.amount)
            remaining -= covered
            excess = cl.amount - covered
            if excess > 0 and cl.date:
                key = cl.date.strftime('%Y-%m')
                monthly[key] = monthly.get(key, 0.0) + excess

        currency = self.currency_id or self.company_id.currency_id
        moves = self.env['account.move']
        for key in sorted(monthly):
            amount = currency.round(monthly[key])
            if not amount:
                continue
            year, month = int(key[:4]), int(key[5:])
            entry_date = datetime.date(year, month, calendar.monthrange(year, month)[1])
            ref = _('Commission True-up - %s %s', self.employee_id.name, key)
            moves |= self.env['account.move'].create({
                'move_type': 'entry',
                'journal_id': prepaid_journal.id,
                'date': entry_date,
                'ref': ref,
                'line_ids': [
                    (0, 0, {'name': ref, 'account_id': expense_account.id,
                            'debit': amount, 'credit': 0.0}),
                    (0, 0, {'name': ref, 'account_id': prepaid_account.id,
                            'debit': 0.0, 'credit': amount}),
                ],
            })
        if moves:
            moves.action_post()
            bill.write({'deferred_move_ids': [fields.Command.link(m.id) for m in moves]})
            bill.message_post(body=_(
                '%(count)d monthly expense entries posted (Dr %(exp)s / Cr %(pre)s), '
                'matching the commission months.',
                count=len(moves), exp=expense_account.display_name,
                pre=prepaid_account.display_name,
            ))

    def _get_cash_payments(self):
        """All effective outbound payments for this year (linked + via bills)."""
        self.ensure_one()
        payments = self.payment_ids | self.bill_ids.matched_payment_ids
        return payments.filtered(
            lambda p: p.payment_type == 'outbound' and p.state in ('in_process', 'paid')
        )

    @api.depends(
        'payment_ids', 'payment_ids.state', 'payment_ids.amount', 'payment_ids.payment_type',
        'payment_ids.currency_id',
        'bill_ids.matched_payment_ids', 'bill_ids.matched_payment_ids.state',
        'minimum_amount',
        'scheme_id.commission_line_ids.state', 'scheme_id.commission_line_ids.amount',
        'scheme_id.commission_line_ids.date_year',
    )
    def _compute_cash_payments(self):
        for rec in self:
            payments = rec._get_cash_payments()
            rec.payment_count = len(payments)
            # Sum in the scheme currency — payments may be in another currency
            # (e.g. USD): convert each at its own payment date.
            total = 0.0
            for p in payments:
                if p.currency_id and rec.currency_id and p.currency_id != rec.currency_id:
                    total += p.currency_id._convert(
                        p.amount, rec.currency_id,
                        rec.company_id or self.env.company,
                        p.date or fields.Date.today(),
                    )
                else:
                    total += p.amount
            rec.amount_paid_cash = total
            # Due follows the confirmation doctrine: only CONFIRMED commission
            # (or the contractual guarantee, whichever is higher) is owed.
            confirmed = sum(rec._year_commission_lines().filtered(
                lambda l: l.state in ('confirmed', 'paid')).mapped('amount'))
            rec.amount_due_year = max(confirmed, rec.minimum_amount)
            # Rounding write-offs reduce what remains payable
            wo_moves = self.env['account.move'].search([
                ('commission_year_id', '=', rec.id),
                ('commission_writeoff', '=', True),
                ('state', '=', 'posted'),
            ])
            # Net of both directions: underpay write-offs debit the payable
            # (positive), overpay roundings credit it (negative).
            rec.writeoff_total = sum(
                l.debit - l.credit for m in wo_moves for l in m.line_ids
                if l.account_id.account_type == 'liability_payable')
            rec.outstanding_cash = rec.amount_due_year - rec.amount_paid_cash - rec.writeoff_total

    _year_uniq = models.Constraint(
        'unique(scheme_id, year)',
        'A year configuration already exists for this employee and year!',
    )

    @api.depends('employee_id', 'year')
    def _compute_display_name(self):
        for rec in self:
            if rec.employee_id and rec.year:
                rec.display_name = f"{rec.employee_id.name} - {rec.year}"
            else:
                rec.display_name = _('New Year')

    @api.depends(
        'scheme_id.commission_line_ids',
        'scheme_id.commission_line_ids.amount',
        'scheme_id.commission_line_ids.state',
        'scheme_id.commission_line_ids.date_year',
        'minimum_amount',
        'year',
    )
    def _compute_totals(self):
        for rec in self:
            lines = rec.scheme_id.commission_line_ids.filtered(
                lambda l: l.date_year == rec.year and l.state != 'cancelled'
            )
            rec.total_earned = sum(lines.mapped('amount'))
            rec.total_paid = sum(lines.filtered(lambda l: l.state == 'paid').mapped('amount'))
            rec.total_pending = sum(lines.filtered(lambda l: l.state == 'pending').mapped('amount'))
            rec.shortfall = max(0.0, rec.minimum_amount - rec.total_earned)
            rec.outstanding = max(0.0, rec.total_earned - rec.total_paid)

    @api.depends('bill_ids')
    def _compute_bill_count(self):
        for rec in self:
            rec.bill_count = len(rec.bill_ids)

    @api.depends('bill_ids', 'bill_ids.commission_offset_amount', 'minimum_amount',
                 'scheme_id.commission_line_ids.state', 'scheme_id.commission_line_ids.amount',
                 'scheme_id.commission_line_ids.date_year')
    def _compute_advance(self):
        for rec in self:
            # The guarantee advance is consumed by the offsets applied on the
            # excess (true-up) bills — the moment confirmed earnings above the
            # guarantee get billed, the coverage is used up.
            consumed = sum(rec.bill_ids.mapped('commission_offset_amount'))
            rec.advance_consumed = consumed
            rec.advance_remaining = max(0.0, rec.minimum_amount - consumed)
            # Earned above the guarantee (confirmed only) — what the employee is
            # owed beyond the advance.
            confirmed = sum(rec._year_commission_lines().filtered(
                lambda l: l.state in ('confirmed', 'paid')).mapped('amount'))
            rec.payable_to_employee = max(0.0, confirmed - rec.minimum_amount)

    @api.constrains('production_rate')
    def _check_rate(self):
        for rec in self:
            if rec.production_rate < 0 or rec.production_rate > 100:
                raise ValidationError(_('Commission rate must be between 0 and 100%.'))

    def action_close_year(self):
        """Close the year: lock all commission lines.

        Warn only when something REAL is open: unapproved (pending) lines or
        cash still owed. Line-level 'paid' state is not the criterion — payment
        happens at year level (bills + payments + write-offs).
        """
        self.ensure_one()
        if self.state == 'closed':
            raise UserError(_('This year is already closed.'))

        pending = self._year_commission_lines().filtered(lambda l: l.state == 'pending')
        if pending or self.outstanding_cash > 0.01:
            # Return a confirmation wizard
            return {
                'type': 'ir.actions.act_window',
                'name': _('Close Year - Open Items'),
                'res_model': 'vpa.commission.close.year.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_scheme_year_id': self.id,
                    'default_unpaid_count': len(pending),
                    'default_unpaid_amount': max(0.0, self.outstanding_cash),
                },
            }
        self._do_close_year()

    def _do_close_year(self):
        """Actually close the year — lock lines and set state."""
        self.ensure_one()
        lines = self.scheme_id.commission_line_ids.filtered(
            lambda l: l.date_year == self.year and l.state != 'cancelled'
        )
        # A fully settled year marks its confirmed lines as paid — the cash went
        # out at year level, so the line states should say so.
        if self.outstanding_cash <= 0.01:
            lines.filtered(lambda l: l.state == 'confirmed').write({
                'state': 'paid',
                'paid_date': fields.Date.today(),
                'paid_by': self.env.uid,
            })
        lines.write({'year_locked': True})
        self.write({'state': 'closed'})
        self._log_year_event(_(
            'CLOSED — %(count)d line(s) locked, outstanding %(out)s, '
            '%(pending)d unapproved') % {
                'count': len(lines),
                'out': f'{self.outstanding_cash:,.2f}',
                'pending': len(lines.filtered(lambda l: l.state == 'pending')),
            })

    def _log_year_event(self, message):
        """Log a traceability event in the year's chatter (author + timestamp
        are recorded natively by the message)."""
        self.ensure_one()
        self.message_post(body=message)

    def action_reopen_year(self):
        """Reopen a closed year — requires a reason (traceability)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reopen Year - %s (%s)', self.employee_id.name, self.year),
            'res_model': 'vpa.commission.reopen.year.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_scheme_year_id': self.id},
        }

    def _do_reopen_year(self, reason):
        """Unlock the year's lines and log who reopened it and why."""
        self.ensure_one()
        lines = self.scheme_id.commission_line_ids.filtered(
            lambda l: l.date_year == self.year
        )
        lines.write({'year_locked': False})
        self.write({'state': 'open'})
        self._log_year_event(_('REOPENED — reason: %s —', reason))

    def action_open_year(self):
        """Open this year's full record (Commission Centre detail form)."""
        self.ensure_one()
        return {
            'name': self.display_name,
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.commission.scheme.year',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    def action_view_commission_lines(self):
        """Open commission lines for this year."""
        self.ensure_one()
        return {
            'name': _('Commission Lines - %s (%s)', self.employee_id.name, self.year),
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.commission.line',
            'view_mode': 'list,pivot,graph,form',
            'domain': [
                ('scheme_id', '=', self.scheme_id.id),
                ('date_year', '=', self.year),
                ('state', '!=', 'cancelled'),
            ],
        }

    def action_view_bills(self):
        """Open vendor bills for this year."""
        self.ensure_one()
        return {
            'name': _('Bills - %s (%s)', self.employee_id.name, self.year),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('commission_year_id', '=', self.id)],
        }

    def action_register_payment(self):
        """Open the year payment wizard (pay the employee for this year)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Pay Commission - %s (%s)', self.employee_id.name, self.year),
            'res_model': 'vpa.commission.pay.year.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_scheme_year_id': self.id,
            },
        }

    def action_view_payments(self):
        """Open all cash payments for this year (linked + via bills)."""
        self.ensure_one()
        payments = self.payment_ids | self.bill_ids.matched_payment_ids
        list_view = self.env.ref('vpa_sales_commission.view_account_payment_list_commission')
        return {
            'name': _('Payments - %s (%s)', self.employee_id.name, self.year),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'views': [(list_view.id, 'list'), (False, 'form')],
            'domain': [('id', 'in', payments.ids)],
            'context': {'create': False},
        }

    def action_view_mos(self):
        """Open all Manufacturing Orders behind this year's commission."""
        self.ensure_one()
        mo_ids = self._year_commission_lines().mapped('production_id').ids
        return {
            'name': _('Manufacturing Orders - %s (%s)', self.employee_id.name, self.year),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': [('id', 'in', mo_ids)],
            'context': {'create': False},
        }

    def action_view_sos(self):
        """Open all Sales Orders behind this year's commission."""
        self.ensure_one()
        so_names = {n for n in self._year_commission_lines().mapped('sale_order_name') if n}
        orders = self.env['sale.order'].search([('name', 'in', list(so_names))])
        return {
            'name': _('Sales Orders - %s (%s)', self.employee_id.name, self.year),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', orders.ids)],
            'context': {'create': False},
        }

    def action_generate_bill(self):
        """Open bill generation wizard for this year.

        Defaults to the guarantee ('base') bill: one vendor bill to the employee
        for the year's minimum guarantee, with the expense spread over 12 monthly
        deferred entries (Jan–Dec of the year).
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generate Commission Bill'),
            'res_model': 'vpa.commission.bill.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_scheme_id': self.scheme_id.id,
                'default_year': self.year,
                'default_bill_type': 'base',
            },
        }


class VpaCommissionReopenYearWizard(models.TransientModel):
    _name = 'vpa.commission.reopen.year.wizard'
    _description = 'Reopen Commission Year'

    scheme_year_id = fields.Many2one(
        'vpa.commission.scheme.year',
        string='Commission Year',
        required=True,
    )
    reason = fields.Text(
        string='Reason',
        required=True,
        help='Why is this closed year being reopened? Logged permanently in the '
             'year\'s notes together with your name and the timestamp.',
    )

    def action_reopen(self):
        self.ensure_one()
        if self.scheme_year_id.state != 'closed':
            raise UserError(_('This year is not closed.'))
        self.scheme_year_id._do_reopen_year(self.reason)
        return {'type': 'ir.actions.act_window_close'}


class VpaCommissionCloseYearWizard(models.TransientModel):
    _name = 'vpa.commission.close.year.wizard'
    _description = 'Close Year Confirmation'

    scheme_year_id = fields.Many2one(
        'vpa.commission.scheme.year',
        string='Scheme Year',
        required=True,
    )
    unpaid_count = fields.Integer(string='Unpaid Lines', readonly=True)
    unpaid_amount = fields.Float(string='Unpaid Amount', digits=(12, 2), readonly=True)
    currency_id = fields.Many2one(
        'res.currency',
        related='scheme_year_id.currency_id',
    )

    def action_confirm_close(self):
        """Confirm closing the year despite unpaid lines."""
        self.ensure_one()
        self.scheme_year_id._do_close_year()
        return {'type': 'ir.actions.act_window_close'}
