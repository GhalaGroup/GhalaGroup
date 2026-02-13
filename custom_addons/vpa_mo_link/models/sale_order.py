# -*- coding: utf-8 -*-
from odoo import models, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_create_remaining_mo(self):
        """
        Create Manufacturing Orders for remaining quantities.

        Calculates the difference between SO line quantities and existing MO quantities,
        then creates new MOs for any remaining quantities.
        """
        self.ensure_one()

        # Build mapping: product_id -> remaining quantity
        remaining_products = []

        for line in self.order_line:
            if not line.product_id or line.product_id.type == 'service':
                continue

            so_qty = line.product_uom_qty

            # Get total MO quantity for this product (exclude cancelled)
            mos = self.env['mrp.production'].search([
                ('origin', '=', self.name),
                ('product_id', '=', line.product_id.id),
                ('state', '!=', 'cancel')
            ])
            mo_qty = sum(mo.product_qty for mo in mos)

            # Calculate remaining
            remaining = so_qty - mo_qty
            if remaining > 0:
                remaining_products.append({
                    'product': line.product_id,
                    'remaining_qty': remaining,
                    'line': line,
                })

        if not remaining_products:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Remaining Quantities'),
                    'message': _('All products have MOs covering the full SO quantities.'),
                    'type': 'info',
                    'sticky': False,
                }
            }

        # Create MOs for remaining quantities
        created_mos = []

        for item in remaining_products:
            product = item['product']
            qty = item['remaining_qty']

            # Find BOM for product
            bom = self.env['mrp.bom']._bom_find(
                products=product,
                company_id=self.company_id.id,
                bom_type='normal'
            )

            # Get BOM from the result (it's a dict with product as key)
            bom_id = bom.get(product, False)

            # Create MO with context to preserve quantity
            mo = self.env['mrp.production'].with_context(
                vpa_explicit_product_qty=qty
            ).create({
                'product_id': product.id,
                'product_qty': qty,
                'bom_id': bom_id.id if bom_id else False,
                'origin': self.name,
                'company_id': self.company_id.id,
            })
            created_mos.append(mo.name)

        # Post message on Sale Order
        message = _(
            'Created %d Manufacturing Order(s) for remaining quantities: %s'
        ) % (len(created_mos), ', '.join(created_mos))
        self.message_post(body=message)

        # Show success notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('MOs Created'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    @api.depends('stock_reference_ids.production_ids', 'name')
    def _compute_mrp_production_ids(self):
        """
        Override sale_mrp's compute method to include both:
        1. Automatically created MOs (via stock_reference_ids from sale_mrp)
        2. Manually linked MOs (via origin field match)

        This allows MOs created BEFORE the Sales Order to appear in the smart button
        when their Source/Origin field matches the SO name.
        """
        # Call parent method to get automatically created MOs
        super()._compute_mrp_production_ids()

        # Add manually created MOs where origin matches SO name
        for sale in self:
            # Search for MOs with matching origin
            origin_mos = self.env['mrp.production'].search([
                ('origin', '=', sale.name),
                ('state', '!=', 'cancel'),
                ('id', 'not in', sale.mrp_production_ids.ids)  # Avoid duplicates
            ])

            # Add them to the computed field
            if origin_mos:
                sale.mrp_production_ids |= origin_mos
                sale.mrp_production_count = len(sale.mrp_production_ids)

    @property
    def procurement_group_id(self):
        """
        Dummy property for compatibility with Manufacturing Order automations.

        This property prevents AttributeError when automations try to access
        procurement_group_id field without checking if sale_stock module is installed.

        Returns:
            False: Always returns False since the real field doesn't exist

        Note:
            The real procurement_group_id field is added by the sale_stock module.
            This dummy property allows automations to check the field without crashing.
        """
        return False
