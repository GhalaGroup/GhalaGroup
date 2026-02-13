# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Link existing MO finished moves to pending delivery moves.

    When MOs were created via "Create Remaining MO", their finished moves
    were not linked to the pending delivery moves (MTO chain). This caused
    "Check Availability" to fail on deliveries even when stock was available.
    """
    cr.execute("""
        SELECT sp.id, sp.name, sp.origin
        FROM stock_picking sp
        JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
        WHERE sp.state NOT IN ('done', 'cancel')
          AND spt.code = 'outgoing'
          AND sp.origin IS NOT NULL
          AND sp.origin LIKE 'S%%'
    """)
    pending_pickings = cr.fetchall()

    total_links = 0

    for picking_id, picking_name, origin in pending_pickings:
        # Get delivery moves for this picking
        cr.execute("""
            SELECT sm.id, sm.product_id
            FROM stock_move sm
            WHERE sm.picking_id = %s
              AND sm.state NOT IN ('done', 'cancel')
        """, (picking_id,))
        delivery_moves = cr.fetchall()

        for delivery_move_id, product_id in delivery_moves:
            # Find MO finished moves for same product and origin, not already linked
            cr.execute("""
                SELECT smf.id
                FROM stock_move smf
                JOIN mrp_production mp ON smf.production_id = mp.id
                WHERE mp.origin = %s
                  AND smf.product_id = %s
                  AND mp.state != 'cancel'
                  AND smf.id NOT IN (
                      SELECT move_orig_id FROM stock_move_move_rel WHERE move_dest_id = %s
                  )
            """, (origin, product_id, delivery_move_id))
            unlinked_finished_moves = cr.fetchall()

            for (finished_move_id,) in unlinked_finished_moves:
                cr.execute("""
                    INSERT INTO stock_move_move_rel (move_orig_id, move_dest_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (finished_move_id, delivery_move_id))
                total_links += 1

    if total_links:
        _logger.info("VPA MO Link: Linked %d MO finished moves to delivery moves", total_links)
