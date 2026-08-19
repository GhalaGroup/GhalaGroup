# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.


def migrate(cr, version):
    """Cancelled MOs never owe commission — backfill existing data.

    From 19.0.2.3.1, cancelling an MO cancels its pending commission lines
    and its commission status computes to Not Applicable automatically. This
    applies the same outcome to MOs cancelled before the upgrade, so nobody
    has to press "Mark Not Applicable" on old cancelled orders.
    """
    if not version:
        return
    # Drop pending commission of cancelled MOs (closed years stay immutable).
    cr.execute("""
        UPDATE vpa_commission_line l
        SET state = 'cancelled'
        FROM mrp_production mp
        WHERE mp.id = l.production_id
          AND mp.state = 'cancel'
          AND l.state = 'pending'
          AND COALESCE(l.year_locked, FALSE) = FALSE
    """)
    # Recompute the stored status for cancelled MOs with no active commission.
    cr.execute("""
        UPDATE mrp_production mp
        SET commission_status = 'not_applicable'
        WHERE mp.state = 'cancel'
          AND COALESCE(mp.commission_blocked, FALSE) = FALSE
          AND NOT EXISTS (
              SELECT 1 FROM vpa_commission_line l
              WHERE l.production_id = mp.id AND l.state != 'cancelled'
          )
    """)
