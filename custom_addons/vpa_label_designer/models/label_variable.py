# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class LabelVariable(models.Model):
    _name = 'vpa.label.variable'
    _description = 'Label Variable Definition'
    _order = 'category, name'

    name = fields.Char(string='Variable Name', required=True,
                       help='Variable name used in templates, e.g. PRODUCT_NAME')
    display_name_custom = fields.Char(string='Display Name',
                                      help='Friendly display name for the variable')
    category = fields.Selection([
        ('product', 'Product'),
        ('stock', 'Stock / Lot'),
        ('manufacturing', 'Manufacturing'),
        ('purchase', 'Purchase'),
        ('alt_uom', 'Alternative UoM'),
        ('company', 'Company'),
        ('custom', 'Custom'),
    ], string='Category', required=True, default='product')

    model_name = fields.Char(string='Source Model',
                             help='Technical model name, e.g. product.product')
    field_path = fields.Char(string='Field Path',
                             help='Dot-notation field path, e.g. product_id.categ_id.name')
    sample_value = fields.Char(string='Sample Value',
                               help='Value used for preview rendering')
    is_system = fields.Boolean(string='System Variable', default=False,
                               help='System variables cannot be deleted by users')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'Variable name must be unique.'),
    ]

    def name_get(self):
        result = []
        for rec in self:
            label = rec.display_name_custom or rec.name
            result.append((rec.id, f"{label} ({{{{{rec.name}}}}})" ))
        return result

    def resolve_value(self, record, extra_values=None):
        """Resolve this variable's value from a record.

        Args:
            record: The Odoo record to resolve against
            extra_values: Optional dict of extra variable values (e.g., alt UoM data)

        Returns:
            str: The resolved value or empty string
        """
        self.ensure_one()

        # Check extra_values first (e.g., ALT_UOM_BARCODE from wizard)
        if extra_values and self.name in extra_values:
            return str(extra_values[self.name])

        if not self.field_path or not record:
            # Alt UoM variables have no field_path — they only get values via extra_values.
            # When no alt UoM is selected, fall back to standard product packaging.
            if self.category == 'alt_uom':
                try:
                    product = self._get_product(record)
                    if product:
                        tmpl = product.product_tmpl_id if product._name == 'product.product' else product
                        # Read from VPA UoM conversions - find first one with packaging info
                        conversions = getattr(tmpl, 'uom_conversion_ids', None)
                        conv = None
                        if conversions:
                            # Prefer conversion with packaging_name set
                            conv = next((c for c in conversions if c.packaging_name), None)
                            if not conv:
                                conv = conversions[0]
                        if conv:
                            if self.name == 'QTY_PER_PACKAGE':
                                qty = conv.qty_per_package or 0
                                return str(int(qty)) if qty == int(qty) else str(qty)
                            if self.name == 'PACKAGING_NAME':
                                return conv.packaging_name or conv.uom_id.name or ''
                except Exception:
                    pass
                return ''
            return self.sample_value or ''

        # Handle special computed variables
        if self.field_path.startswith('__compute_'):
            return self._resolve_computed(record, extra_values)

        try:
            obj = record
            for field_name in self.field_path.split('.'):
                if hasattr(obj, field_name):
                    obj = getattr(obj, field_name)
                else:
                    return self.sample_value or ''
            if obj is False or obj is None:
                return ''
            # Format price fields with currency
            if self.name in ('PRODUCT_PRICE', 'PRODUCT_PRICE_INCL'):
                return self._format_price(obj, record)
            return str(obj)
        except Exception:
            return self.sample_value or ''

    def _format_price(self, amount, record):
        """Format a numeric amount with thousand separators and currency symbol."""
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return str(amount)
        # Get currency from product or company
        currency = None
        if hasattr(record, 'currency_id') and record.currency_id:
            currency = record.currency_id
        elif hasattr(record, 'product_id') and record.product_id and record.product_id.currency_id:
            currency = record.product_id.currency_id
        if not currency:
            currency = self.env.company.currency_id
        # Format: 45,000.00 TZS
        formatted = '{:,.{prec}f}'.format(amount, prec=currency.decimal_places if currency else 2)
        symbol = currency.symbol if currency else ''
        if currency and currency.position == 'before':
            price_str = f'{symbol} {formatted}'
        else:
            price_str = f'{formatted} {symbol}'.strip()
        return price_str

    def _resolve_computed(self, record, extra_values=None):
        """Resolve specially computed variables that can't use simple field paths."""
        self.ensure_one()
        try:
            if self.field_path == '__compute_price_incl__':
                return self._compute_price_incl(record)
            if self.field_path == '__compute_variant__':
                return self._compute_variant(record)
            if self.field_path == '__compute_variant_full__':
                return self._compute_variant_full(record)
        except Exception:
            pass
        return self.sample_value or ''

    def _get_product(self, record):
        """Get the product.product record from any supported source record."""
        if record._name == 'product.product':
            return record
        if hasattr(record, 'product_id') and record.product_id:
            return record.product_id
        return None

    def _compute_variant(self, record):
        """Get variant attribute values like 'Large, Red'."""
        product = self._get_product(record)
        if not product:
            return self.sample_value or ''
        if hasattr(product, 'product_template_attribute_value_ids'):
            ptavs = product.product_template_attribute_value_ids
            if ptavs:
                # _get_combination_name() returns '' for single-variant products in Odoo 19
                # Fall back to reading attribute values directly
                name = ptavs._get_combination_name()
                if not name:
                    name = ', '.join(
                        ptav.product_attribute_value_id.name
                        for ptav in ptavs
                        if ptav.product_attribute_value_id
                    )
                return name or ''
        return ''

    def _compute_variant_full(self, record):
        """Get full product name with variant like 'Office Chair (Large, Red)'."""
        product = self._get_product(record)
        if not product:
            return self.sample_value or ''
        variant = ''
        if hasattr(product, 'product_template_attribute_value_ids'):
            ptavs = product.product_template_attribute_value_ids
            if ptavs:
                variant = ptavs._get_combination_name()
        name = product.name or ''
        if variant:
            return f'{name} ({variant})'
        return name

    def _compute_price_incl(self, record):
        """Compute tax-inclusive sales price for a product."""
        product = self._get_product(record)
        if not product:
            return self.sample_value or ''

        price = product.lst_price
        if not product.taxes_id:
            return self._format_price(price, product)

        tax_result = product.taxes_id.compute_all(
            price_unit=price,
            currency=product.currency_id,
            product=product,
        )
        amount = tax_result.get('total_included', price)
        return self._format_price(amount, product)
