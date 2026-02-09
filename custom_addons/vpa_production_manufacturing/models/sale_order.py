# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_sync_delivery_quantities(self):
        """
        Synchronize delivery order quantities with current sale order line quantities.

        When sale order quantities are adjusted after delivery orders have been created,
        this function updates all related delivery orders to match the new quantities.
        """
        self.ensure_one()

        if not self.picking_ids:
            raise UserError(_('No delivery orders found for this sale order.'))

        # Build mapping of product_id -> sale order quantity
        so_qty_map = {}
        for line in self.order_line:
            if line.product_id:
                so_qty_map[line.product_id.id] = line.product_uom_qty

        updated_pickings = []
        updated_move_count = 0

        for picking in self.picking_ids:
            # Skip cancelled pickings
            if picking.state == 'cancel':
                continue

            picking_updated = False

            for move in picking.move_ids:
                if move.product_id.id in so_qty_map:
                    new_qty = so_qty_map[move.product_id.id]
                    old_qty = move.product_uom_qty

                    if old_qty != new_qty:
                        move.write({'product_uom_qty': new_qty})
                        picking_updated = True
                        updated_move_count += 1

            if picking_updated:
                updated_pickings.append(picking.name)

        if updated_pickings:
            message = _('%d move(s) updated in %d delivery order(s): %s') % (
                updated_move_count,
                len(updated_pickings),
                ', '.join(updated_pickings)
            )
            self.message_post(body=message)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Delivery Quantities Synced'),
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Updates Needed'),
                    'message': _('All delivery quantities already match the sale order.'),
                    'type': 'info',
                    'sticky': False,
                }
            }
