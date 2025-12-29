# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, models, _


class UomUom(models.Model):
    """Extend uom.uom to support quick creation from conversion form."""
    _inherit = 'uom.uom'

    @api.model
    def name_create(self, name):
        """Create a new UoM with just a name.

        This is called when user types a new UoM name in the Alternative UoM
        field and selects "Create". The UoM is created with:
        - relative_factor = 1.0 (neutral - actual conversion is on product)
        - No reference unit (it's a base unit itself)

        The actual conversion factor is stored in product.uom.conversion,
        not in the UoM itself. This follows the SAP approach where UoMs
        are global but conversions are product-specific.
        """
        # Check if UoM with this name already exists (case-insensitive)
        existing = self.search([('name', '=ilike', name)], limit=1)
        if existing:
            return existing.id, existing.display_name

        # Create new UoM with factor 1 (neutral)
        # In Odoo 19, UoMs don't have categories anymore
        new_uom = self.create({
            'name': name,
            'relative_factor': 1.0,
            # No relative_uom_id means this is a reference unit
        })
        return new_uom.id, new_uom.display_name

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        """Enhanced search to find UoMs by name."""
        domain = domain or []
        if name:
            domain = ['|', ('name', operator, name)] + domain
        return self._search(domain, limit=limit, order=order)
