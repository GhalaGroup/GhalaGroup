# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductUomConversion(models.Model):
    """Product-specific UoM conversion factors.

    This model stores alternative units of measure with product-specific
    conversion factors, similar to SAP's Alternative Unit of Measure (AUoM).

    Key feature: Auto-creates UoM if it doesn't exist when user types a new name.
    """
    _name = 'product.uom.conversion'
    _description = 'Product UoM Conversion'
    _order = 'sequence, id'

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Used to order alternative UoMs. First one is the primary alternative.",
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product Template',
        required=True,
        ondelete='cascade',
        index=True,
    )
    name = fields.Char(
        string='Description',
        help="Optional description for this conversion (e.g., 'Full board 1220x2440mm')",
    )

    # Alternative UoM - can select existing or create new
    uom_id = fields.Many2one(
        'uom.uom',
        string='Alternative UoM',
        required=True,
        help="Select an existing UoM or type a new name to create one.",
    )

    base_uom_id = fields.Many2one(
        'uom.uom',
        string='Base UoM',
        related='product_tmpl_id.uom_id',
        store=True,
        readonly=True,
        help="The base unit of measure of the product (storage unit).",
    )

    # Conversion: alt_qty (Alternative UoM) = base_qty (Base UoM)
    alt_qty = fields.Float(
        string='Alt. Qty',
        required=True,
        default=1.0,
        digits='Product Unit of Measure',
        help="Quantity in alternative UoM (e.g., 1 for '1 Board')",
    )
    base_qty = fields.Float(
        string='Base Qty',
        required=True,
        default=1.0,
        digits='Product Unit of Measure',
        help="Equivalent quantity in base UoM (e.g., 2.9768 for '2.9768 m²')",
    )

    # Computed factor for conversions
    factor = fields.Float(
        string='Conversion Factor',
        compute='_compute_factor',
        store=True,
        digits=(16, 10),
        help="Factor to convert from alternative UoM to base UoM. "
             "base_qty = alt_qty * factor",
    )
    inverse_factor = fields.Float(
        string='Inverse Factor',
        compute='_compute_factor',
        store=True,
        digits=(16, 10),
        help="Factor to convert from base UoM to alternative UoM. "
             "alt_qty = base_qty * inverse_factor",
    )

    # Rounding precision
    rounding = fields.Float(
        string='Rounding Precision',
        default=0.01,
        digits=(16, 6),
        help="Rounding precision for quantities in this alternative UoM.",
    )

    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
        help="Company this conversion belongs to. Leave empty to share across all companies.",
    )

    # SQL Constraints using Odoo 19 syntax
    _unique_product_uom_company = models.Constraint(
        'UNIQUE(product_tmpl_id, uom_id, company_id)',
        'An alternative UoM can only be defined once per product per company!',
    )
    _check_alt_qty_positive = models.Constraint(
        'CHECK(alt_qty > 0)',
        'Alternative quantity must be positive!',
    )
    _check_base_qty_positive = models.Constraint(
        'CHECK(base_qty > 0)',
        'Base quantity must be positive!',
    )

    @api.depends('alt_qty', 'base_qty')
    def _compute_factor(self):
        for conv in self:
            if conv.alt_qty and conv.base_qty:
                conv.factor = conv.base_qty / conv.alt_qty
                conv.inverse_factor = conv.alt_qty / conv.base_qty
            else:
                conv.factor = 0.0
                conv.inverse_factor = 0.0

    @api.constrains('uom_id', 'product_tmpl_id')
    def _check_not_base_uom(self):
        """Ensure alternative UoM is different from base UoM."""
        for conv in self:
            if conv.uom_id == conv.product_tmpl_id.uom_id:
                raise ValidationError(_(
                    "Alternative UoM cannot be the same as the product's base UoM."
                ))

    @api.depends('name', 'uom_id', 'uom_id.name', 'alt_qty', 'base_qty', 'base_uom_id', 'base_uom_id.name')
    def _compute_display_name(self):
        """Compute display name for Odoo 19 (replaces name_get)."""
        for conv in self:
            if conv.uom_id and conv.base_uom_id:
                display = f"{conv.uom_id.name} ({conv.alt_qty} = {conv.base_qty} {conv.base_uom_id.name})"
                if conv.name:
                    display = f"{conv.name} - {display}"
                conv.display_name = display
            else:
                conv.display_name = conv.name or _("New Conversion")

    def convert_to_base(self, qty):
        """Convert quantity from alternative UoM to base UoM.

        Args:
            qty: Quantity in alternative UoM

        Returns:
            Quantity in base UoM
        """
        self.ensure_one()
        return qty * self.factor

    def convert_from_base(self, qty, round_result=True):
        """Convert quantity from base UoM to alternative UoM.

        Args:
            qty: Quantity in base UoM
            round_result: Whether to apply rounding

        Returns:
            Quantity in alternative UoM
        """
        self.ensure_one()
        result = qty * self.inverse_factor
        if round_result and self.rounding:
            result = float(round(result / self.rounding) * self.rounding)
        return result
