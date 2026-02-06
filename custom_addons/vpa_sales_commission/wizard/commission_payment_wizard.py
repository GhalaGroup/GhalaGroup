# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError


class CommissionPaymentWizard(models.TransientModel):
    _name = 'vpa.commission.payment.wizard'
    _description = 'Commission Payment Wizard'

    commission_line_ids = fields.Many2many(
        'vpa.commission.line',
        string='Commission Lines',
        readonly=True,
    )
    line_count = fields.Integer(
        string='Number of Lines',
        compute='_compute_totals',
    )
    total_amount = fields.Float(
        string='Total Commission',
        digits=(12, 2),
        compute='_compute_totals',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        required=True,
        domain="[('type', '=', 'general')]",
    )
    expense_account_id = fields.Many2one(
        'account.account',
        string='Expense Account',
        required=True,
        help='Debit account - commission expense',
    )
    payable_account_id = fields.Many2one(
        'account.account',
        string='Payable Account',
        required=True,
        help='Credit account - commission payable',
    )
    payment_date = fields.Date(
        string='Payment Date',
        required=True,
        default=fields.Date.context_today,
    )
    summary_line_ids = fields.One2many(
        'vpa.commission.payment.wizard.summary',
        'wizard_id',
        string='Employee Summary',
    )

    @api.depends('commission_line_ids')
    def _compute_totals(self):
        for wizard in self:
            wizard.line_count = len(wizard.commission_line_ids)
            wizard.total_amount = sum(wizard.commission_line_ids.mapped('amount'))

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            raise UserError(_('No commission lines selected.'))

        lines = self.env['vpa.commission.line'].browse(active_ids)

        # Validate all lines are confirmed
        non_confirmed = lines.filtered(lambda l: l.state != 'confirmed')
        if non_confirmed:
            raise UserError(_(
                'Only confirmed commission lines can be paid. '
                'The following lines are not confirmed: %s'
            ) % ', '.join(non_confirmed.mapped('name')))

        res['commission_line_ids'] = [Command.set(lines.ids)]

        # Load defaults from settings
        ICP = self.env['ir.config_parameter'].sudo()
        journal_id = ICP.get_param('vpa_sales_commission.journal_id', '')
        if journal_id:
            res['journal_id'] = int(journal_id)

        # Determine default accounts based on commission type
        # If all lines are production type, use production accounts
        # If mixed or sales, use production accounts as fallback
        line_types = set(lines.mapped('type'))
        if line_types == {'sales'}:
            expense_param = 'vpa_sales_commission.sales_expense_account_id'
            payable_param = 'vpa_sales_commission.sales_payable_account_id'
        else:
            expense_param = 'vpa_sales_commission.production_expense_account_id'
            payable_param = 'vpa_sales_commission.production_payable_account_id'

        expense_id = ICP.get_param(expense_param, '')
        payable_id = ICP.get_param(payable_param, '')
        if expense_id:
            res['expense_account_id'] = int(expense_id)
        if payable_id:
            res['payable_account_id'] = int(payable_id)

        # Build employee summary
        employee_data = {}
        for line in lines:
            emp_id = line.employee_id.id
            if emp_id not in employee_data:
                employee_data[emp_id] = {
                    'employee_id': emp_id,
                    'line_count': 0,
                    'total_amount': 0.0,
                    'currency_id': line.currency_id.id or self.env.company.currency_id.id,
                }
            employee_data[emp_id]['line_count'] += 1
            employee_data[emp_id]['total_amount'] += line.amount

        res['summary_line_ids'] = [Command.create(data) for data in employee_data.values()]

        return res

    @api.onchange('commission_line_ids')
    def _onchange_commission_line_ids(self):
        """Build employee summary lines."""
        summary_vals = []
        employee_data = {}
        for line in self.commission_line_ids:
            emp_id = line.employee_id.id
            if emp_id not in employee_data:
                employee_data[emp_id] = {
                    'employee_id': emp_id,
                    'line_count': 0,
                    'total_amount': 0.0,
                    'currency_id': line.currency_id.id or self.currency_id.id,
                }
            employee_data[emp_id]['line_count'] += 1
            employee_data[emp_id]['total_amount'] += line.amount

        for data in employee_data.values():
            summary_vals.append(Command.create(data))

        self.summary_line_ids = [Command.clear()] + summary_vals

    def action_create_payment(self):
        """Create journal entries grouped by employee and mark lines as paid."""
        self.ensure_one()

        if not self.commission_line_ids:
            raise UserError(_('No commission lines to pay.'))

        # Re-validate all lines are confirmed
        non_confirmed = self.commission_line_ids.filtered(lambda l: l.state != 'confirmed')
        if non_confirmed:
            raise UserError(_(
                'Only confirmed commission lines can be paid. '
                'The following lines are not confirmed: %s'
            ) % ', '.join(non_confirmed.mapped('name')))

        # Group lines by employee
        employee_groups = {}
        for line in self.commission_line_ids:
            emp_id = line.employee_id.id
            if emp_id not in employee_groups:
                employee_groups[emp_id] = self.env['vpa.commission.line']
            employee_groups[emp_id] |= line

        created_moves = self.env['account.move']

        for emp_id, emp_lines in employee_groups.items():
            employee = emp_lines[0].employee_id
            total_amount = sum(emp_lines.mapped('amount'))

            if total_amount <= 0:
                continue

            # Build reference
            ref_parts = [employee.name]
            dates = emp_lines.mapped('date')
            if dates:
                min_date = min(dates)
                max_date = max(dates)
                if min_date.month == max_date.month and min_date.year == max_date.year:
                    ref_parts.append(min_date.strftime('%B %Y'))
                else:
                    ref_parts.append(f"{min_date.strftime('%b %Y')} - {max_date.strftime('%b %Y')}")
            ref = 'Commission Payment: ' + ' - '.join(ref_parts)

            # Get partner from employee
            partner_id = False
            if hasattr(employee, 'work_contact_id') and employee.work_contact_id:
                partner_id = employee.work_contact_id.id

            move_vals = {
                'move_type': 'entry',
                'date': self.payment_date,
                'journal_id': self.journal_id.id,
                'ref': ref,
                'line_ids': [
                    Command.create({
                        'name': f'Commission Expense: {employee.name}',
                        'account_id': self.expense_account_id.id,
                        'debit': total_amount,
                        'credit': 0.0,
                        'partner_id': partner_id,
                    }),
                    Command.create({
                        'name': f'Commission Payable: {employee.name}',
                        'account_id': self.payable_account_id.id,
                        'debit': 0.0,
                        'credit': total_amount,
                        'partner_id': partner_id,
                    }),
                ],
            }

            move = self.env['account.move'].create(move_vals)
            created_moves |= move

            # Mark commission lines as paid and link to journal entry
            emp_lines.write({
                'state': 'paid',
                'paid_date': self.payment_date,
                'paid_by': self.env.uid,
                'payment_move_id': move.id,
            })

        move_count = len(created_moves)
        line_count = len(self.commission_line_ids)

        # Return notification with link to journal entries
        if move_count == 1:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Payment Created'),
                    'message': _('%d commission line(s) paid. 1 journal entry created.') % line_count,
                    'type': 'success',
                    'sticky': False,
                    'next': {
                        'type': 'ir.actions.act_window',
                        'name': _('Payment Journal Entry'),
                        'res_model': 'account.move',
                        'view_mode': 'form',
                        'res_id': created_moves[0].id,
                    },
                },
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Payments Created'),
                    'message': _('%d commission line(s) paid. %d journal entries created.') % (line_count, move_count),
                    'type': 'success',
                    'sticky': False,
                    'next': {
                        'type': 'ir.actions.act_window',
                        'name': _('Payment Journal Entries'),
                        'res_model': 'account.move',
                        'view_mode': 'list,form',
                        'domain': [('id', 'in', created_moves.ids)],
                    },
                },
            }


class CommissionPaymentWizardSummary(models.TransientModel):
    _name = 'vpa.commission.payment.wizard.summary'
    _description = 'Commission Payment Wizard Summary'

    wizard_id = fields.Many2one(
        'vpa.commission.payment.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        readonly=True,
    )
    line_count = fields.Integer(
        string='Lines',
        readonly=True,
    )
    total_amount = fields.Float(
        string='Total Commission',
        digits=(12, 2),
        readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        readonly=True,
    )
