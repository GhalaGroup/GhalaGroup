# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CommissionChangeDateWizard(models.TransientModel):
    _name = 'vpa.commission.change.date.wizard'
    _description = 'Change Commission Date'

    new_date = fields.Date(
        string='New Date',
        required=True,
        default=fields.Date.today,
        help='This date will be written to every selected commission line. '
             'The Year/Month used across reports and guarantees update automatically.',
    )
    reason = fields.Text(
        string='Reason',
        help='Optional. Recorded in each line\'s Notes for audit.',
    )
    line_ids = fields.Many2many(
        'vpa.commission.line',
        string='Commission Lines',
        readonly=True,
    )
    line_count = fields.Integer(
        string='Lines to Change',
        compute='_compute_line_count',
    )
    old_date_display = fields.Char(
        string='Current Date',
        compute='_compute_line_count',
        help='The date currently on the selected commission(s). '
             'Shows a range when the selection spans several dates.',
    )
    source_summary = fields.Char(
        string='Selection',
        readonly=True,
        help='What was selected to open this wizard.',
    )

    @api.depends('line_ids', 'line_ids.date')
    def _compute_line_count(self):
        for wiz in self:
            wiz.line_count = len(wiz.line_ids)
            dates = sorted({d for d in wiz.line_ids.mapped('date') if d})
            if not dates:
                wiz.old_date_display = False
            elif len(dates) == 1:
                wiz.old_date_display = fields.Date.to_string(dates[0])
            else:
                wiz.old_date_display = _('%(count)d dates: %(first)s … %(last)s') % {
                    'count': len(dates),
                    'first': fields.Date.to_string(dates[0]),
                    'last': fields.Date.to_string(dates[-1]),
                }

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids') or []
        CommissionLine = self.env['vpa.commission.line']
        lines = CommissionLine.browse()
        summary = ''

        if active_model == 'vpa.commission.line':
            lines = CommissionLine.browse(active_ids).exists()
            summary = _('%d commission line(s) selected') % len(lines)

        elif active_model == 'mrp.production.commission.report':
            reports = self.env['mrp.production.commission.report'].browse(active_ids).exists()
            production_ids = reports.mapped('production_id').ids
            lines = CommissionLine.search([
                ('production_id', 'in', production_ids),
                ('state', '!=', 'cancelled'),
            ])
            summary = _('%d manufacturing order(s) selected') % len(production_ids)

        elif active_model == 'so.commission.report':
            reports = self.env['so.commission.report'].browse(active_ids).exists()
            domain = ['|'] * (len(reports) - 1) if len(reports) > 1 else []
            for rep in reports:
                # Report rows are keyed by (sale_order_name, employee, company).
                # Resolve back to the exact underlying lines using that same key.
                so_name = False if rep.sale_order_name == 'No SO' else rep.sale_order_name
                domain += [
                    '&', '&',
                    ('sale_order_name', '=', so_name),
                    ('employee_id', '=', rep.employee_id.id),
                    ('company_id', '=', rep.company_id.id),
                ]
            if domain:
                domain += [('state', '!=', 'cancelled')]
                lines = CommissionLine.search(domain)
            summary = _('%d sales order group(s) selected') % len(reports)

        res['line_ids'] = [(6, 0, lines.ids)]
        res['source_summary'] = summary
        return res

    def action_change_date(self):
        self.ensure_one()
        lines = self.line_ids
        if not lines:
            raise UserError(_('No commission lines to update.'))

        # Block year-locked lines (reuse the model's own guard).
        lines._check_year_locked()

        # Block paid lines — changing their date would desync accounting.
        paid = lines.filtered(lambda l: l.state == 'paid')
        if paid:
            raise UserError(_(
                'Paid commission lines cannot have their date changed. '
                'Reset them to pending first: %s',
                ', '.join(paid.mapped('name'))
            ))

        stamp = _('Date changed %(old)s → %(new)s by %(user)s on %(when)s')
        today = fields.Date.today()
        user_name = self.env.user.name
        for line in lines:
            note = stamp % {
                'old': line.date or _('unset'),
                'new': self.new_date,
                'user': user_name,
                'when': today,
            }
            if self.reason:
                note += ': ' + self.reason
            existing = line.notes or ''
            line.write({
                'date': self.new_date,
                'notes': (existing + '\n' + note).strip() if existing else note,
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Date Changed'),
                'message': _('%(count)d commission line(s) moved to %(date)s.') % {
                    'count': len(lines),
                    'date': self.new_date,
                },
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
