# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

"""
Stock Barcode Integration for VPA UoM Conversions.

This module extends the stock barcode scanning functionality to recognize
barcodes assigned to VPA alternative UoM conversions. When a VPA conversion
barcode is scanned, it returns the linked product with the VPA-specific
conversion factor.

Only loaded when stock_barcode module is installed.
"""

from odoo import api, models


class ProductUomConversion(models.Model):
    """Extend product.uom.conversion for stock barcode scanning support."""
    _inherit = 'product.uom.conversion'
    _barcode_field = 'barcode'

    @api.model
    def _get_fields_stock_barcode(self):
        """Return fields needed for barcode scanning."""
        return [
            'barcode',
            'product_tmpl_id',
            'uom_id',
            'base_uom_id',
            'alt_qty',
            'base_qty',
            'factor',
            'inverse_factor',
            'qty_per_package',
            'name',
        ]

    def _get_stock_barcode_specific_data(self):
        """Return related product and UoM data for barcode scanning.

        When a VPA conversion barcode is scanned, we need to return:
        - The product (for display and selection)
        - The alternative UoM (for quantity input)
        - The base UoM (for reference)
        """
        products = self.mapped('product_tmpl_id.product_variant_id')
        alt_uoms = self.mapped('uom_id')
        base_uoms = self.mapped('base_uom_id')
        all_uoms = alt_uoms | base_uoms

        return {
            'product.product': products.read(
                self.env['product.product']._get_fields_stock_barcode()
                if hasattr(self.env['product.product'], '_get_fields_stock_barcode')
                else ['id', 'display_name', 'barcode', 'tracking', 'uom_id'],
                load=False
            ),
            'uom.uom': all_uoms.read(
                self.env['uom.uom']._get_fields_stock_barcode()
                if hasattr(self.env['uom.uom'], '_get_fields_stock_barcode')
                else ['id', 'name', 'category_id', 'factor', 'rounding'],
                load=False
            ),
        }
