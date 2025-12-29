# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class VpaUom(models.Model):
    """VPA Unit of Measure - Our own UoM management.

    This is a standalone UoM model that doesn't depend on Odoo's uom.uom.
    Create UoMs here, then assign them to products.
    """
    _name = 'vpa.uom'
    _description = 'VPA Unit of Measure'
    _order = 'name'

    name = fields.Char(
        string='Unit Name',
        required=True,
        help="Name of the unit (e.g., Board 2440x1220, Pallet, Box)",
    )

    # Conversion to base unit
    factor = fields.Float(
        string='Conversion Factor',
        required=True,
        default=1.0,
        digits=(16, 6),
        help="How many base units equal 1 of this unit.\n"
             "Example: If 1 Board = 2.9768 m², enter 2.9768",
    )

    base_uom_name = fields.Char(
        string='Base Unit',
        required=True,
        default='Units',
        help="The base unit this converts to (e.g., m², kg, Units, Liters)",
    )

    description = fields.Text(
        string='Description',
        help="Optional description or notes about this unit",
    )

    active = fields.Boolean(default=True)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        help="Leave empty to share across all companies",
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name, company_id)',
         'Unit name must be unique per company!'),
        ('factor_positive', 'CHECK(factor > 0)',
         'Conversion factor must be positive!'),
    ]

    def _compute_display_name(self):
        for uom in self:
            if uom.factor != 1.0:
                uom.display_name = f"{uom.name} (1 = {uom.factor} {uom.base_uom_name})"
            else:
                uom.display_name = uom.name
