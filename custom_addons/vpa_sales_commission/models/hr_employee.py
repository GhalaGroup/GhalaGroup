# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    commission_scheme_ids = fields.One2many(
        'vpa.commission.scheme',
        'employee_id',
        string='Commission Schemes',
    )
    commission_line_ids = fields.One2many(
        'vpa.commission.line',
        'employee_id',
        string='Commission Lines',
    )
    commission_count = fields.Integer(
        string='Commission Lines',
        compute='_compute_commission_count',
    )
    commission_total = fields.Float(
        string='Total Commission',
        compute='_compute_commission_count',
    )
    has_commission_scheme = fields.Boolean(
        string='Has Commission Scheme',
        compute='_compute_commission_count',
    )

    def _compute_commission_count(self):
        commission_data = self.env['vpa.commission.line'].sudo().read_group(
            [('employee_id', 'in', self.ids), ('state', '!=', 'cancelled')],
            ['employee_id', 'amount'],
            ['employee_id'],
        )
        mapped_data = {
            item['employee_id'][0]: {
                'count': item['employee_id_count'],
                'total': item['amount'],
            }
            for item in commission_data
        }
        scheme_employees = set(
            self.env['vpa.commission.scheme'].sudo().search(
                [('employee_id', 'in', self.ids), ('active', '=', True)]
            ).mapped('employee_id.id')
        )
        for employee in self:
            data = mapped_data.get(employee.id, {})
            employee.commission_count = data.get('count', 0)
            employee.commission_total = data.get('total', 0.0)
            employee.has_commission_scheme = employee.id in scheme_employees

    def action_view_commission_lines(self):
        """Open commission lines for this employee."""
        self.ensure_one()
        return {
            'name': _('Commission Lines - %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.commission.line',
            'view_mode': 'list,pivot,graph,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {},
        }
