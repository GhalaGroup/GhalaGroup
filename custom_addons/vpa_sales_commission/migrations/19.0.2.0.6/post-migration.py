# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """v2.0.6: repair fossil commission_status values on MOs.

    Early versions stored 'blocked' / 'pending' — values that no longer exist
    in the selection, so those MOs displayed an empty status and matched no
    filter. Recompute the status from the actual data (blocked flag + lines).
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute("""SELECT id FROM mrp_production
                  WHERE commission_status NOT IN
                        ('none','not_applicable','applied','paid','cancelled')
                     OR commission_status IS NULL""")
    ids = [r[0] for r in cr.fetchall()]
    if ids:
        mos = env['mrp.production'].browse(ids)
        mos._compute_commission_status()
        _logger.info('Commission migration: repaired commission_status on %d MO(s).', len(ids))
