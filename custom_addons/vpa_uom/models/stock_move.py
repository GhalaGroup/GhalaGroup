# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    # Override allowed_uom_ids to include product-specific alternative UoMs
    allowed_uom_ids = fields.Many2many(
        'uom.uom',
        compute='_compute_allowed_uom_ids',
    )

    # Display field for alternative UoM quantity
    qty_alt_uom = fields.Float(
        string='Alt. UoM Qty',
        compute='_compute_qty_alt_uom',
        digits='Product Unit of Measure',
        help="Quantity in primary alternative UoM for display.",
    )
    qty_alt_uom_str = fields.Char(
        string='Alt. Qty',
        compute='_compute_qty_alt_uom',
        help="Formatted quantity in alternative UoM.",
    )
    primary_alt_uom_id = fields.Many2one(
        'uom.uom',
        string='Primary Alt. UoM',
        related='product_id.product_tmpl_id.primary_alt_uom_id',
    )

    @api.depends('product_id', 'product_id.uom_id', 'product_id.uom_ids',
                 'product_id.seller_ids', 'product_id.product_tmpl_id.uom_conversion_ids')
    def _compute_allowed_uom_ids(self):
        """Include product-specific alternative UoMs in allowed UoMs."""
        for move in self:
            if not move.product_id:
                move.allowed_uom_ids = self.env['uom.uom']
                continue

            # Start with product's base UoM
            uoms = move.product_id.uom_id

            # Add standard Odoo packagings (uom_ids)
            uoms |= move.product_id.uom_ids

            # Add supplier UoMs
            uoms |= move.product_id.seller_ids.mapped('product_uom_id')

            # Add VPA alternative UoMs
            uoms |= move.product_id.product_tmpl_id.uom_conversion_ids.mapped('uom_id')

            move.allowed_uom_ids = uoms

    @api.depends('product_uom_qty', 'product_id', 'product_id.product_tmpl_id.primary_alt_uom_id',
                 'product_id.product_tmpl_id.uom_conversion_ids')
    def _compute_qty_alt_uom(self):
        """Compute quantity in primary alternative UoM for display."""
        for move in self:
            tmpl = move.product_id.product_tmpl_id if move.product_id else False
            if tmpl and tmpl.primary_alt_uom_id and tmpl.uom_conversion_ids:
                conversion = tmpl.uom_conversion_ids.filtered(
                    lambda c: c.uom_id == tmpl.primary_alt_uom_id
                )[:1]
                if conversion:
                    alt_qty = conversion.convert_from_base(move.product_uom_qty)
                    move.qty_alt_uom = alt_qty
                    if alt_qty == int(alt_qty):
                        move.qty_alt_uom_str = f"≈ {int(alt_qty)} {tmpl.primary_alt_uom_id.name}"
                    else:
                        move.qty_alt_uom_str = f"≈ {alt_qty:.2f} {tmpl.primary_alt_uom_id.name}"
                    continue
            move.qty_alt_uom = 0.0
            move.qty_alt_uom_str = ''

    def _get_product_uom_qty(self, product_qty, product_uom):
        """Override to use product-specific conversion if available.

        This method converts from the document UoM to the product's base UoM.
        """
        self.ensure_one()
        if not self.product_id:
            return super()._get_product_uom_qty(product_qty, product_uom)

        # Check for product-specific conversion
        conversion = self.product_id.get_uom_conversion(product_uom)
        if conversion:
            return conversion.convert_to_base(product_qty)

        # Fall back to standard conversion
        return product_uom._compute_quantity(product_qty, self.product_id.uom_id)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    # Display field for alternative UoM quantity
    qty_alt_uom_str = fields.Char(
        string='Alt. Qty',
        compute='_compute_qty_alt_uom',
        help="Formatted quantity in alternative UoM.",
    )

    @api.depends('quantity', 'product_id', 'product_id.product_tmpl_id.primary_alt_uom_id',
                 'product_id.product_tmpl_id.uom_conversion_ids')
    def _compute_qty_alt_uom(self):
        """Compute quantity in primary alternative UoM for display."""
        for line in self:
            tmpl = line.product_id.product_tmpl_id if line.product_id else False
            if tmpl and tmpl.primary_alt_uom_id and tmpl.uom_conversion_ids:
                conversion = tmpl.uom_conversion_ids.filtered(
                    lambda c: c.uom_id == tmpl.primary_alt_uom_id
                )[:1]
                if conversion:
                    alt_qty = conversion.convert_from_base(line.quantity)
                    if alt_qty == int(alt_qty):
                        line.qty_alt_uom_str = f"≈ {int(alt_qty)} {tmpl.primary_alt_uom_id.name}"
                    else:
                        line.qty_alt_uom_str = f"≈ {alt_qty:.2f} {tmpl.primary_alt_uom_id.name}"
                    continue
            line.qty_alt_uom_str = ''
