# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.fields import Command


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _should_auto_confirm_procurement_mo(self, p):
        """
        Override to prevent automatic confirmation of Manufacturing Orders.

        Standard Odoo behavior auto-confirms MOs in certain conditions.
        This override ensures ALL automatically created MOs stay in DRAFT state
        so users can review, set BOM if missing, and manually confirm.

        Returns:
            bool: Always False to keep MOs in draft state
        """
        # Always return False to keep MOs in draft for user review
        return False

    def _prepare_mo_vals(self, product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values, bom):
        """
        Override to allow MO creation even when BOM is not found.

        Standard Odoo fails or skips MO creation if no BOM exists.
        This override creates a basic MO structure without BOM,
        allowing users to manually set the BOM later.

        Args:
            bom: Bill of Materials (can be False if not found)

        Returns:
            dict: MO values for creation
        """
        if not bom:
            # No BOM found - create basic MO structure
            # User will need to manually set BOM before confirming
            picking_type = self.picking_type_id
            date_planned = fields.Datetime.from_string(values.get('date_planned', fields.Datetime.now()))

            return {
                'origin': origin,
                'product_id': product_id.id,
                'product_qty': product_qty,
                'product_uom_id': product_uom.id,
                'location_src_id': picking_type.default_location_src_id.id if picking_type else False,
                'location_dest_id': picking_type.default_location_dest_id.id or location_dest_id.id if picking_type else location_dest_id.id,
                'location_final_id': location_dest_id.id,
                'bom_id': False,  # User will set this manually
                'date_deadline': date_planned,
                'date_start': date_planned,
                'reference_ids': [Command.set(values.get('reference_ids', self.env['stock.reference']).ids)],
                'picking_type_id': picking_type.id if picking_type else values.get('warehouse_id') and values['warehouse_id'].manu_type_id.id,
                'company_id': company_id.id,
                'move_dest_ids': values.get('move_dest_ids') and [(4, x.id) for x in values['move_dest_ids']] or False,
                'user_id': False,
            }

        # Call parent method if BOM exists
        return super()._prepare_mo_vals(product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values, bom)
