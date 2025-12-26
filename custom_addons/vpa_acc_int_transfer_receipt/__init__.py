# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from . import models
from . import wizard


def _load_vpa_layout_template(env):
    """
    Post-init hook to load VPA layout report template if the layout module is installed.
    This allows the receipt module to work independently of vpa_acc_int_transfer_layout.
    """
    # Check if vpa_acc_int_transfer_layout is installed
    layout_module = env['ir.module.module'].search([
        ('name', '=', 'vpa_acc_int_transfer_layout'),
        ('state', '=', 'installed'),
    ], limit=1)

    if layout_module:
        # Load the VPA layout template
        from odoo.tools import convert_file
        convert_file(
            env,
            'vpa_acc_int_transfer_receipt',
            'report/transfer_report_template_vpa.xml',
            None,
            mode='init',
            kind='data',
        )
