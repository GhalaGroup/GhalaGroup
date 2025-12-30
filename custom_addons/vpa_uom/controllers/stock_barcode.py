# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

"""
Stock Barcode Controller Extension for VPA UoM Conversions.

This controller extends the stock barcode scanning functionality to include
VPA alternative UoM conversions in barcode searches. When a VPA conversion
barcode is scanned, the system will return the associated product and
conversion data.

Only active when stock_barcode module is installed.
"""

from odoo import http
from odoo.http import request

try:
    from odoo.addons.stock_barcode.controllers.stock_barcode import StockBarcodeController

    class VpaStockBarcodeController(StockBarcodeController):
        """Extend stock barcode controller to search VPA conversion barcodes."""

        def _get_barcode_field_by_model(self):
            """Add product.uom.conversion to the list of models searched for barcodes.

            This allows VPA conversion barcodes to be found when scanning.
            """
            result = super()._get_barcode_field_by_model()
            # Add VPA conversion model if it has barcode field
            if hasattr(request.env['product.uom.conversion'], '_barcode_field'):
                result['product.uom.conversion'] = request.env['product.uom.conversion']._barcode_field
            return result

        def _try_open_product_location(self, barcode):
            """Extended to also search VPA conversion barcodes.

            If barcode matches a VPA conversion, open the product's stock locations.
            """
            # First try parent implementation
            result = super()._try_open_product_location(barcode)
            if result:
                return result

            # Try VPA conversion barcode
            conversion = request.env['product.uom.conversion'].search([
                ('barcode', '=', barcode),
                ('active', '=', True),
            ], limit=1)

            if conversion:
                product = conversion.product_tmpl_id.product_variant_id
                if product:
                    tree_view_id = request.env.ref('stock.view_stock_quant_tree').id
                    kanban_view_id = request.env.ref('stock_barcode.stock_quant_barcode_kanban_2').id
                    return {
                        'action': {
                            'name': product.display_name,
                            'res_model': 'stock.quant',
                            'views': [(kanban_view_id, 'kanban'), (tree_view_id, 'list')],
                            'type': 'ir.actions.act_window',
                            'domain': [('product_id', '=', product.id)],
                            'context': {
                                'search_default_internal_loc': True,
                                'vpa_conversion_id': conversion.id,
                                'vpa_conversion_factor': conversion.factor,
                                'vpa_conversion_uom_id': conversion.uom_id.id,
                            },
                        }
                    }
            return False

except ImportError:
    # stock_barcode module not installed - provide empty placeholder
    pass
