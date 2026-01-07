# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    # Primary alternative UoM from product
    primary_alt_uom_id = fields.Many2one(
        'uom.uom',
        string='Alt. UoM',
        compute='_compute_alt_uom_qty',
        store=True,
        help="Primary alternative unit of measure for this product.",
    )

    # Quantity in alternative UoM
    qty_alt_uom = fields.Float(
        string='Alt. Qty',
        compute='_compute_alt_uom_qty',
        store=True,
        digits='Product Unit of Measure',
        help="Quantity in primary alternative UoM.",
    )

    qty_alt_uom_str = fields.Char(
        string='Alt. Qty Display',
        compute='_compute_alt_uom_qty',
        store=True,
        help="Formatted quantity in alternative UoM.",
    )

    # All alternative UoM quantities (for reports showing all conversions)
    qty_all_alt_uom = fields.Char(
        string='All Alt. UoMs',
        compute='_compute_all_alt_uom_qty',
        store=True,
        help="Quantity in all alternative UoMs (formatted for display).",
    )

    @api.depends('quantity', 'product_id', 'product_id.product_tmpl_id.primary_alt_uom_id',
                 'product_id.product_tmpl_id.uom_conversion_ids',
                 'product_id.product_tmpl_id.uom_conversion_ids.factor')
    def _compute_alt_uom_qty(self):
        """Compute quantity in primary alternative UoM."""
        for quant in self:
            tmpl = quant.product_id.product_tmpl_id if quant.product_id else False
            if tmpl and tmpl.primary_alt_uom_id and tmpl.uom_conversion_ids:
                conversion = tmpl.uom_conversion_ids.filtered(
                    lambda c: c.uom_id == tmpl.primary_alt_uom_id
                )[:1]
                if conversion:
                    alt_qty = conversion.convert_from_base(quant.quantity)
                    quant.primary_alt_uom_id = tmpl.primary_alt_uom_id
                    quant.qty_alt_uom = alt_qty
                    if alt_qty == int(alt_qty):
                        quant.qty_alt_uom_str = str(int(alt_qty))
                    else:
                        quant.qty_alt_uom_str = f"{alt_qty:.2f}"
                    continue
            quant.primary_alt_uom_id = False
            quant.qty_alt_uom = 0.0
            quant.qty_alt_uom_str = ''

    @api.depends('quantity', 'product_id',
                 'product_id.product_tmpl_id.uom_conversion_ids',
                 'product_id.product_tmpl_id.uom_conversion_ids.uom_id',
                 'product_id.product_tmpl_id.uom_conversion_ids.factor',
                 'product_id.product_tmpl_id.uom_conversion_ids.sequence')
    def _compute_all_alt_uom_qty(self):
        """Compute quantity in ALL alternative UoMs as a formatted string."""
        for quant in self:
            tmpl = quant.product_id.product_tmpl_id if quant.product_id else False
            if tmpl and tmpl.uom_conversion_ids:
                parts = []
                for conversion in tmpl.uom_conversion_ids.sorted('sequence'):
                    alt_qty = conversion.convert_from_base(quant.quantity)
                    if alt_qty == int(alt_qty):
                        parts.append(f"{int(alt_qty)} {conversion.uom_id.name}")
                    else:
                        parts.append(f"{alt_qty:.2f} {conversion.uom_id.name}")
                quant.qty_all_alt_uom = " | ".join(parts) if parts else ''
            else:
                quant.qty_all_alt_uom = ''
