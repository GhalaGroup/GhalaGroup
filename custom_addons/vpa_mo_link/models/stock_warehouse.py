# -*- coding: utf-8 -*-
from odoo import models, api


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    @api.model
    def _create_production_route_rules(self):
        """
        Ensure the Production route has manufacturing rules for each warehouse.
        Called during module installation/upgrade.
        """
        # Find or create the Production route
        production_route = self.env.ref('vpa_mo_link.route_production', raise_if_not_found=False)

        if not production_route:
            return

        # Get all active warehouses
        warehouses = self.search([])

        for warehouse in warehouses:
            # Check if a manufacturing rule already exists for this warehouse on the Production route
            existing_rule = self.env['stock.rule'].search([
                ('route_id', '=', production_route.id),
                ('picking_type_id', '=', warehouse.manu_type_id.id),
                ('action', '=', 'manufacture')
            ], limit=1)

            if existing_rule:
                continue  # Rule already exists

            # Only create rule if warehouse has manufacturing enabled
            if not warehouse.manu_type_id:
                continue

            # Create manufacturing rule for this warehouse
            self.env['stock.rule'].create({
                'name': f"{warehouse.code}: Manufacture - Draft MO",
                'action': 'manufacture',
                'route_id': production_route.id,
                'picking_type_id': warehouse.manu_type_id.id,
                'location_dest_id': warehouse.lot_stock_id.id,
                'warehouse_id': warehouse.id,
                'procure_method': 'make_to_order',
                'company_id': warehouse.company_id.id,
                'propagate_cancel': True,
            })
