# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Recompute the stored line settlement figures under the new doctrine.

    From 19.0.2.6.0, a commission line's amount_paid is its PROPORTIONAL
    share of how settled its year is (cash moves at year level), instead of
    all-or-nothing on the line's own 'paid' state. The columns are stored —
    the SQL analysis views aggregate them — so every existing line must be
    re-derived once; afterwards the payment-side mutation hooks keep them
    fresh.
    """
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    Line = env['vpa.commission.line']
    lines = Line.search([])
    env.add_to_compute(Line._fields['amount_paid'], lines)
    env.add_to_compute(Line._fields['amount_due'], lines)
    Line.flush_model()
