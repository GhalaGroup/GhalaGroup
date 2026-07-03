# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _action_done(self):
        """Snapshot document-level on-hand and requested quantity per
        (product, source location) BEFORE Odoo decrements stock in sub-steps.

        Odoo removes stock through several `_update_available_quantity` calls
        per move line, so by the time the Stock Sentinel quant hook fires the
        on-hand it sees is already partially drawn down. This snapshot lets the
        hook report the numbers the user actually entered on the document.
        """
        snapshot = {}
        for ml in self:
            product = ml.product_id
            location = ml.location_id
            if not product.is_storable or location.usage != 'internal':
                continue
            qty = ml.quantity_product_uom
            if product.uom_id.compare(qty, 0) <= 0:
                continue
            key = (product.id, location.id)
            if key not in snapshot:
                # Physical on-hand (SUM of quant.quantity), i.e. the "On Hand"
                # figure the user sees - NOT the available quantity, which is
                # already net of reservations made by this very move.
                quants = self.env['stock.quant'].sudo()._gather(
                    product, location, strict=False)
                on_hand = sum(quants.mapped('quantity'))
                snapshot[key] = {'on_hand': on_hand, 'requested': 0.0}
            snapshot[key]['requested'] += qty

        if snapshot:
            self = self.with_context(nns_snapshot=snapshot)
        return super(StockMoveLine, self)._action_done()
