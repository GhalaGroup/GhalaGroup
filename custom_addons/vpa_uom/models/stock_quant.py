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
