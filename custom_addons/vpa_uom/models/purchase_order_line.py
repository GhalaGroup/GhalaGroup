# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Override allowed UoMs to include product-specific alternatives
    allowed_uom_ids = fields.Many2many(
        'uom.uom',
        compute='_compute_allowed_uom_ids',
        help="UoMs available for selection (base + alternatives + supplier UoMs).",
    )

    # Display field for base UoM equivalent
    qty_base_uom = fields.Float(
        string='Base Qty',
        compute='_compute_qty_base_uom',
        digits='Product Unit of Measure',
        help="Quantity in product's base UoM (for stock impact).",
    )
    qty_base_uom_str = fields.Char(
        string='Stock Impact',
        compute='_compute_qty_base_uom',
        help="Formatted quantity showing stock impact in base UoM.",
    )

    @api.depends('product_id', 'product_id.uom_id', 'product_id.uom_ids',
                 'product_id.seller_ids', 'product_id.seller_ids.product_uom_id',
                 'product_id.product_tmpl_id.uom_conversion_ids')
    def _compute_allowed_uom_ids(self):
        """Include product-specific alternative UoMs in allowed UoMs."""
        for line in self:
            if not line.product_id:
                line.allowed_uom_ids = self.env['uom.uom']
                continue

            tmpl = line.product_id.product_tmpl_id

            # Start with product's base UoM
            uoms = tmpl.uom_id

            # Add standard Odoo packagings (uom_ids)
            uoms |= tmpl.uom_ids

            # Add supplier UoMs
            uoms |= line.product_id.seller_ids.mapped('product_uom_id')

            # Add VPA alternative UoMs
            uoms |= tmpl.uom_conversion_ids.mapped('uom_id')

            line.allowed_uom_ids = uoms

    @api.depends('product_qty', 'product_uom_id', 'product_id')
    def _compute_qty_base_uom(self):
        """Compute quantity in base UoM for stock impact display."""
        for line in self:
            if not line.product_id or not line.product_uom_id:
                line.qty_base_uom = line.product_qty
                line.qty_base_uom_str = ''
                continue

            tmpl = line.product_id.product_tmpl_id
            base_uom = tmpl.uom_id

            # If already in base UoM, no conversion needed
            if line.product_uom_id == base_uom:
                line.qty_base_uom = line.product_qty
                line.qty_base_uom_str = ''
                continue

            # Check for product-specific conversion
            conversion = tmpl.get_uom_conversion(line.product_uom_id)
            if conversion:
                base_qty = conversion.convert_to_base(line.product_qty)
            else:
                # Fall back to standard Odoo conversion
                base_qty = line.product_uom_id._compute_quantity(
                    line.product_qty, base_uom
                )

            line.qty_base_uom = base_qty
            if base_qty == int(base_qty):
                line.qty_base_uom_str = f"≡ {int(base_qty)} {base_uom.name}"
            else:
                line.qty_base_uom_str = f"≡ {base_qty:.4f} {base_uom.name}"

    def _compute_qty_to_receive(self):
        """Override to use product-specific conversion if available."""
        super()._compute_qty_to_receive()

    def _get_product_purchase_description(self, product_lang):
        """Override to handle alternative UoM in description if needed."""
        return super()._get_product_purchase_description(product_lang)

    @api.onchange('product_uom_id')
    def _onchange_product_uom_id(self):
        """Update price when UoM changes, using product-specific conversion."""
        if not self.product_id or not self.product_uom_id:
            return

        # Check for product-specific conversion
        tmpl = self.product_id.product_tmpl_id
        conversion = tmpl.get_uom_conversion(self.product_uom_id)

        if conversion:
            # Adjust price based on product-specific conversion
            base_price = self.product_id.standard_price
            # Price per alt UoM = base price * factor
            # (e.g., if 1 Board = 2.9768 m², and price is $15/m²,
            #  then price per Board = $15 * 2.9768 = $44.65)
            self.price_unit = base_price * conversion.factor
        else:
            # Fall back to standard behavior
            pass  # Let standard onchange handle it
