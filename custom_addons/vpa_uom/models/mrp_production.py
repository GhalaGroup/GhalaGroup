# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # Override allowed UoMs to include product-specific alternatives
    allowed_uom_ids = fields.Many2many(
        'uom.uom',
        compute='_compute_allowed_uom_ids',
        help="UoMs available for selection (base + alternatives + BOM UoMs).",
    )

    @api.depends('product_id', 'product_id.uom_id', 'product_id.uom_ids',
                 'product_id.bom_ids.product_uom_id',
                 'product_id.product_tmpl_id.uom_conversion_ids')
    def _compute_allowed_uom_ids(self):
        """Include product-specific alternative UoMs in allowed UoMs."""
        for production in self:
            if not production.product_id:
                production.allowed_uom_ids = self.env['uom.uom']
                continue

            tmpl = production.product_id.product_tmpl_id

            # Start with product's base UoM
            uoms = tmpl.uom_id

            # Add standard Odoo packagings (uom_ids)
            uoms |= tmpl.uom_ids

            # Add BOM UoMs
            uoms |= production.product_id.bom_ids.mapped('product_uom_id')

            # Add VPA alternative UoMs
            uoms |= tmpl.uom_conversion_ids.mapped('uom_id')

            production.allowed_uom_ids = uoms


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    # Override allowed UoMs to include product-specific alternatives
    allowed_uom_ids = fields.Many2many(
        'uom.uom',
        compute='_compute_allowed_uom_ids',
        help="UoMs available for selection (base + alternatives).",
    )

    # Display field for base UoM equivalent
    qty_base_uom = fields.Float(
        string='Base Qty',
        compute='_compute_qty_base_uom',
        digits='Product Unit of Measure',
        help="Quantity in product's base UoM.",
    )
    qty_base_uom_str = fields.Char(
        string='Base Equiv.',
        compute='_compute_qty_base_uom',
        help="Formatted quantity in base UoM.",
    )

    @api.depends('product_id', 'product_id.uom_id', 'product_id.uom_ids',
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

            # Add VPA alternative UoMs
            uoms |= tmpl.uom_conversion_ids.mapped('uom_id')

            line.allowed_uom_ids = uoms

    @api.depends('product_qty', 'product_uom_id', 'product_id')
    def _compute_qty_base_uom(self):
        """Compute quantity in base UoM for display."""
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
                line.qty_base_uom_str = f"= {int(base_qty)} {base_uom.name}"
            else:
                line.qty_base_uom_str = f"= {base_qty:.4f} {base_uom.name}"


class StockMoveRaw(models.Model):
    """Extend raw material moves in manufacturing orders."""
    _inherit = 'stock.move'

    # Alternative UoM display for MO components
    qty_alt_uom_mo = fields.Float(
        string='Alt. UoM Qty (MO)',
        compute='_compute_qty_alt_uom_mo',
        digits='Product Unit of Measure',
        help="Quantity in primary alternative UoM for MO display.",
    )
    qty_alt_uom_mo_str = fields.Char(
        string='Alt. Qty (MO)',
        compute='_compute_qty_alt_uom_mo',
        help="Formatted quantity in alternative UoM for MO.",
    )

    @api.depends('product_uom_qty', 'product_id', 'raw_material_production_id',
                 'product_id.product_tmpl_id.primary_alt_uom_id',
                 'product_id.product_tmpl_id.uom_conversion_ids')
    def _compute_qty_alt_uom_mo(self):
        """Compute quantity in primary alternative UoM for MO components."""
        for move in self:
            # Only for raw materials in MO
            if not move.raw_material_production_id:
                move.qty_alt_uom_mo = 0.0
                move.qty_alt_uom_mo_str = ''
                continue

            tmpl = move.product_id.product_tmpl_id if move.product_id else False
            if tmpl and tmpl.primary_alt_uom_id and tmpl.uom_conversion_ids:
                conversion = tmpl.uom_conversion_ids.filtered(
                    lambda c: c.uom_id == tmpl.primary_alt_uom_id
                )[:1]
                if conversion:
                    alt_qty = conversion.convert_from_base(move.product_uom_qty)
                    move.qty_alt_uom_mo = alt_qty
                    if alt_qty == int(alt_qty):
                        move.qty_alt_uom_mo_str = f"≈ {int(alt_qty)} {tmpl.primary_alt_uom_id.name}"
                    else:
                        move.qty_alt_uom_mo_str = f"≈ {alt_qty:.2f} {tmpl.primary_alt_uom_id.name}"
                    continue
            move.qty_alt_uom_mo = 0.0
            move.qty_alt_uom_mo_str = ''
