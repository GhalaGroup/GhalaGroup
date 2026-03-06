# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    default_printer_id = fields.Many2one(
        'vpa.printer.config',
        string='Default Label Printer',
        domain="[('company_id', 'in', [False, company_id])]",
        help='Your personal default printer for label printing. Overrides the company default.',
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['default_printer_id']

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['default_printer_id']
