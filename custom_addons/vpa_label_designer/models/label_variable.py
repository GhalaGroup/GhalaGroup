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
            return str(obj)
        except Exception:
            return self.sample_value or ''

    def _resolve_computed(self, record, extra_values=None):
        """Resolve specially computed variables that can't use simple field paths."""
        self.ensure_one()
        try:
            if self.field_path == '__compute_price_incl__':
                return self._compute_price_incl(record)
        except Exception:
            pass
        return self.sample_value or ''

    def _compute_price_incl(self, record):
        """Compute tax-inclusive sales price for a product."""
        product = record
        if record._name != 'product.product':
            if hasattr(record, 'product_id') and record.product_id:
                product = record.product_id
            else:
                return self.sample_value or ''

        price = product.lst_price
        if not product.taxes_id:
            return str(price)

        tax_result = product.taxes_id.compute_all(
            price_unit=price,
            currency=product.currency_id,
            product=product,
        )
        return str(tax_result.get('total_included', price))
