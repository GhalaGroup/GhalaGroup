# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.


def migrate(cr, version):
    """Backfill paid_by_close for lines flipped by a pre-2.2.0 year close.

    Before 19.0.2.2.0, closing a settled year flipped its confirmed lines to
    'paid' without any marker; reopening left them claiming paid. The new
    reopen only reverts lines carrying paid_by_close, so without this backfill
    every year closed under the old version reopens with 0 lines reverted —
    the exact bug 2.2.0 fixes would persist for existing data.

    Old flipped lines are identifiable: paid + year-locked, in a closed year,
    with neither a payment nor a bill backing the paid state (lines paid any
    other way always carry payment_id or bill_id).
    """
    if not version:
        return
    cr.execute("""
        UPDATE vpa_commission_line l
        SET paid_by_close = TRUE
        FROM vpa_commission_scheme_year y
        WHERE y.scheme_id = l.scheme_id
          AND y.year = l.date_year
          AND y.state = 'closed'
          AND l.state = 'paid'
          AND l.year_locked = TRUE
          AND l.payment_id IS NULL
          AND l.bill_id IS NULL
          AND COALESCE(l.paid_by_close, FALSE) = FALSE
    """)
