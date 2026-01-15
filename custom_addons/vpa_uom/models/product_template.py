# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    uom_conversion_ids = fields.One2many(
        'product.uom.conversion',
        'product_tmpl_id',
        string='Alternative UoMs',
        help="Product-specific alternative units of measure with custom conversion factors.",
    )
    uom_conversion_count = fields.Integer(
        string='Alternative UoM Count',
        compute='_compute_uom_conversion_count',
    )

    # Primary alternative UoM (first in sequence)
    primary_alt_uom_id = fields.Many2one(
        'uom.uom',
        string='Primary Alt. UoM',
        compute='_compute_primary_alt_uom',
        store=True,
        help="The primary alternative unit of measure for display purposes.",
    )

    # Char field for display in list views (workaround for Odoo 19 optional column issues)
    primary_alt_uom_name = fields.Char(
        string='Alt. UoM',
        related='primary_alt_uom_id.name',
        store=True,
        readonly=True,
    )

    # Computed quantities in alternative UoM
    qty_available_alt = fields.Float(
        string='On Hand (Alt. UoM)',
        compute='_compute_qty_alt',
        digits='Product Unit of Measure',
        help="Quantity on hand in primary alternative UoM.",
    )
    qty_available_alt_str = fields.Char(
        string='On Hand Alt.',
        compute='_compute_qty_alt',
        help="Formatted quantity on hand in primary alternative UoM.",
    )

    # All alternative UoM quantities (for reports showing all conversions)
    qty_available_all_alt = fields.Char(
        string='All Alt. UoM Quantities',
        compute='_compute_qty_all_alt',
        help="Quantity on hand in all alternative UoMs (formatted for display).",
    )

    # Allowed UoMs for selection (base + alternatives)
    allowed_uom_ids = fields.Many2many(
        'uom.uom',
        string='Allowed UoMs',
        compute='_compute_allowed_uom_ids',
        help="UoMs that can be used for this product (base + alternatives).",
    )

    @api.depends('uom_conversion_ids')
    def _compute_uom_conversion_count(self):
        for product in self:
            product.uom_conversion_count = len(product.uom_conversion_ids)

    @api.depends('uom_conversion_ids', 'uom_conversion_ids.sequence')
    def _compute_primary_alt_uom(self):
        for product in self:
            conversions = product.uom_conversion_ids.sorted('sequence')
            product.primary_alt_uom_id = conversions[0].uom_id if conversions else False

    @api.depends('qty_available', 'uom_conversion_ids', 'primary_alt_uom_id')
    def _compute_qty_alt(self):
        for product in self:
            if product.primary_alt_uom_id and product.uom_conversion_ids:
                conversion = product.uom_conversion_ids.filtered(
                    lambda c: c.uom_id == product.primary_alt_uom_id
                )[:1]
                if conversion:
                    alt_qty = conversion.convert_from_base(product.qty_available)
                    product.qty_available_alt = alt_qty
                    # Format with rounding
                    if alt_qty == int(alt_qty):
                        product.qty_available_alt_str = f"≈ {int(alt_qty)} {product.primary_alt_uom_id.name}"
                    else:
                        product.qty_available_alt_str = f"≈ {alt_qty:.2f} {product.primary_alt_uom_id.name}"
                else:
                    product.qty_available_alt = 0.0
                    product.qty_available_alt_str = ''
            else:
                product.qty_available_alt = 0.0
                product.qty_available_alt_str = ''

    @api.depends('qty_available', 'uom_conversion_ids', 'uom_conversion_ids.uom_id',
                 'uom_conversion_ids.factor', 'uom_conversion_ids.sequence')
    def _compute_qty_all_alt(self):
        """Compute quantity in ALL alternative UoMs as a formatted string."""
        for product in self:
            if product.uom_conversion_ids:
                parts = []
                for conversion in product.uom_conversion_ids.sorted('sequence'):
                    alt_qty = conversion.convert_from_base(product.qty_available)
                    if alt_qty == int(alt_qty):
                        parts.append(f"{int(alt_qty)} {conversion.uom_id.name}")
                    else:
                        parts.append(f"{alt_qty:.2f} {conversion.uom_id.name}")
                product.qty_available_all_alt = " | ".join(parts) if parts else ''
            else:
                product.qty_available_all_alt = ''

    @api.depends('uom_id', 'uom_conversion_ids.uom_id')
    def _compute_allowed_uom_ids(self):
        for product in self:
            uoms = product.uom_id
            uoms |= product.uom_conversion_ids.mapped('uom_id')
            product.allowed_uom_ids = uoms

    def get_uom_conversion(self, uom):
        """Get the conversion record for a specific UoM.

        Args:
            uom: uom.uom record

        Returns:
            product.uom.conversion record or False
        """
        self.ensure_one()
        return self.uom_conversion_ids.filtered(lambda c: c.uom_id == uom)[:1]

    def convert_qty_to_base(self, qty, from_uom):
        """Convert quantity from any UoM to base UoM.

        Uses product-specific conversion if available, otherwise
        falls back to standard Odoo UoM conversion.

        Args:
            qty: Quantity to convert
            from_uom: Source UoM record

        Returns:
            Quantity in base UoM
        """
        self.ensure_one()
        if from_uom == self.uom_id:
            return qty

        # Check for product-specific conversion
        conversion = self.get_uom_conversion(from_uom)
        if conversion:
            return conversion.convert_to_base(qty)

        # Fall back to standard Odoo conversion
        return from_uom._compute_quantity(qty, self.uom_id)

    def convert_qty_from_base(self, qty, to_uom, round_result=True):
        """Convert quantity from base UoM to any UoM.

        Uses product-specific conversion if available, otherwise
        falls back to standard Odoo UoM conversion.

        Args:
            qty: Quantity in base UoM
            to_uom: Target UoM record
            round_result: Whether to apply rounding

        Returns:
            Quantity in target UoM
        """
        self.ensure_one()
        if to_uom == self.uom_id:
            return qty

        # Check for product-specific conversion
        conversion = self.get_uom_conversion(to_uom)
        if conversion:
            return conversion.convert_from_base(qty, round_result=round_result)

        # Fall back to standard Odoo conversion
        return self.uom_id._compute_quantity(qty, to_uom, round=round_result)

    def action_view_uom_conversions(self):
        """Open the alternative UoM conversions for this product."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Alternative UoMs'),
            'res_model': 'product.uom.conversion',
            'view_mode': 'list,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {'default_product_tmpl_id': self.id},
        }


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Related field for primary alternative UoM (from template)
    primary_alt_uom_id = fields.Many2one(
        'uom.uom',
        string='Primary Alt. UoM',
        related='product_tmpl_id.primary_alt_uom_id',
        store=True,
    )

    # Char field for display in list views (workaround for Odoo 19 optional column issues)
    primary_alt_uom_name = fields.Char(
        string='Alt. UoM',
        related='primary_alt_uom_id.name',
        store=True,
        readonly=True,
    )

    # Computed quantity in alternative UoM
    qty_available_alt = fields.Float(
        string='On Hand (Alt. UoM)',
        compute='_compute_qty_alt_variant',
        digits='Product Unit of Measure',
    )
    qty_available_alt_str = fields.Char(
        string='On Hand Alt.',
        compute='_compute_qty_alt_variant',
    )

    # All alternative UoM quantities (for reports showing all conversions)
    qty_available_all_alt = fields.Char(
        string='All Alt. UoM Quantities',
        compute='_compute_qty_all_alt_variant',
        help="Quantity on hand in all alternative UoMs (formatted for display).",
    )

    @api.depends('qty_available', 'product_tmpl_id.uom_conversion_ids',
                 'product_tmpl_id.primary_alt_uom_id')
    def _compute_qty_alt_variant(self):
        for product in self:
            tmpl = product.product_tmpl_id
            if tmpl.primary_alt_uom_id and tmpl.uom_conversion_ids:
                conversion = tmpl.uom_conversion_ids.filtered(
                    lambda c: c.uom_id == tmpl.primary_alt_uom_id
                )[:1]
                if conversion:
                    alt_qty = conversion.convert_from_base(product.qty_available)
                    product.qty_available_alt = alt_qty
                    if alt_qty == int(alt_qty):
                        product.qty_available_alt_str = f"≈ {int(alt_qty)} {tmpl.primary_alt_uom_id.name}"
                    else:
                        product.qty_available_alt_str = f"≈ {alt_qty:.2f} {tmpl.primary_alt_uom_id.name}"
                else:
                    product.qty_available_alt = 0.0
                    product.qty_available_alt_str = ''
            else:
                product.qty_available_alt = 0.0
                product.qty_available_alt_str = ''

    @api.depends('qty_available', 'product_tmpl_id.uom_conversion_ids',
                 'product_tmpl_id.uom_conversion_ids.uom_id',
                 'product_tmpl_id.uom_conversion_ids.factor',
                 'product_tmpl_id.uom_conversion_ids.sequence')
    def _compute_qty_all_alt_variant(self):
        """Compute quantity in ALL alternative UoMs as a formatted string."""
        for product in self:
            tmpl = product.product_tmpl_id
            if tmpl and tmpl.uom_conversion_ids:
                parts = []
                for conversion in tmpl.uom_conversion_ids.sorted('sequence'):
                    alt_qty = conversion.convert_from_base(product.qty_available)
                    if alt_qty == int(alt_qty):
                        parts.append(f"{int(alt_qty)} {conversion.uom_id.name}")
                    else:
                        parts.append(f"{alt_qty:.2f} {conversion.uom_id.name}")
                product.qty_available_all_alt = " | ".join(parts) if parts else ''
            else:
                product.qty_available_all_alt = ''

    def get_uom_conversion(self, uom):
        """Get the conversion record for a specific UoM (delegate to template)."""
        self.ensure_one()
        return self.product_tmpl_id.get_uom_conversion(uom)

    def convert_qty_to_base(self, qty, from_uom):
        """Convert quantity to base UoM (delegate to template)."""
        self.ensure_one()
        return self.product_tmpl_id.convert_qty_to_base(qty, from_uom)

    def convert_qty_from_base(self, qty, to_uom, round_result=True):
        """Convert quantity from base UoM (delegate to template)."""
        self.ensure_one()
        return self.product_tmpl_id.convert_qty_from_base(qty, to_uom, round_result=round_result)

    def action_view_uom_conversions(self):
        """Open the alternative UoM conversions for this product (delegate to template)."""
        self.ensure_one()
        return self.product_tmpl_id.action_view_uom_conversions()
