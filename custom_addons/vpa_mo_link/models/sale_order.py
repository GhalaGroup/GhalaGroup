# -*- coding: utf-8 -*-
from odoo import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

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
