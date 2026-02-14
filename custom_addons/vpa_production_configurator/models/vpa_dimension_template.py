# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class VpaDimensionTemplate(models.Model):
    _name = 'vpa.dimension.template'
    _description = 'Dimension Template'
    _order = 'name'

    name = fields.Char(string='Template Name', required=True)
    code = fields.Char(string='Code')
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    calculation_type = fields.Selection([
        ('m2', 'Square Meters (m\u00b2)'),
        ('m3', 'Cubic Meters (m\u00b3)'),
        ('linear_m', 'Linear Meters (m)'),
        ('custom', 'Custom Formula'),
    ], string='Calculation Type', required=True, default='m2')

    quantity_formula = fields.Text(
        string='Quantity Formula',
        default='w_m * h_m',
        help='Python expression to compute quantity. Available variables: dimension codes '
             '(e.g., w, h, d) in original units and with _m suffix for meters (e.g., w_m, h_m).',
    )
    formula_display = fields.Char(
        string='Formula',
        compute='_compute_formula_display',
    )
    default_rate = fields.Float(string='Default Rate', digits='Product Price',
                                help='Default base rate per computed unit (m\u00b2/m\u00b3/m). Can be overridden per product.')

    @api.depends('calculation_type', 'quantity_formula')
    def _compute_formula_display(self):
        labels = {
            'm2': 'Width \u00d7 Height (m\u00b2)',
            'm3': 'Width \u00d7 Height \u00d7 Depth (m\u00b3)',
            'linear_m': 'Length (m)',
        }
        for rec in self:
            if rec.calculation_type in labels:
                rec.formula_display = labels[rec.calculation_type]
            else:
                rec.formula_display = rec.quantity_formula or ''

    @api.onchange('calculation_type')
    def _onchange_calculation_type(self):
        formulas = {
            'm2': 'w_m * h_m',
            'm3': 'w_m * h_m * d_m',
            'linear_m': 'w_m',
        }
        if self.calculation_type in formulas:
            self.quantity_formula = formulas[self.calculation_type]

    dimension_line_ids = fields.One2many('vpa.dimension.template.line', 'template_id', string='Dimensions', copy=True)
    display_group_ids = fields.One2many('vpa.display.group', 'template_id', string='Display Groups', copy=True)
    variable_ids = fields.One2many('vpa.config.variable', 'template_id', string='Configuration Variables', copy=True)

    product_count = fields.Integer(string='Products', compute='_compute_product_count')

    @api.depends('name')
    def _compute_product_count(self):
        for rec in self:
            rec.product_count = self.env['product.template'].search_count([
                ('dimension_template_id', '=', rec.id),
            ])

    def _prepare_eval_context(self, dim_values):
        """Build evaluation context from dimension values.

        Args:
            dim_values: dict of {field_code: value} in the dimension's original UoM
        Returns:
            dict with dimension codes and their _m meter conversions
        """
        context = {}
        for dim_line in self.dimension_line_ids:
            code = dim_line.field_code
            value = dim_values.get(code, dim_line.default_value or 0.0)
            context[code] = value
            # Convert to meters
            if dim_line.uom_type == 'mm':
                context[code + '_m'] = value / 1000.0
            elif dim_line.uom_type == 'cm':
                context[code + '_m'] = value / 100.0
            else:
                context[code + '_m'] = value
        return context

    def evaluate_quantity(self, dim_values):
        """Evaluate the quantity formula with the given dimension values.

        Args:
            dim_values: dict of {field_code: value}
        Returns:
            float: computed quantity (area/volume/length)
        """
        self.ensure_one()
        ctx = self._prepare_eval_context(dim_values)
        try:
            result = safe_eval(self.quantity_formula or '0', ctx, mode='eval')
            return float(result)
        except Exception:
            return 0.0

    def evaluate_price(self, dim_values, rate, config_values=None):
        """Calculate the full unit price including surcharges.

        Args:
            dim_values: dict of {field_code: value}
            rate: base rate per computed unit
            config_values: list of dicts with option data [{option_id, surcharge_type, surcharge_amount, qty_override}]
        Returns:
            float: final unit price
        """
        self.ensure_one()
        computed_qty = self.evaluate_quantity(dim_values)
        per_unit_surcharges = 0.0
        fixed_surcharges = 0.0

        if config_values:
            for cv in config_values:
                if cv.get('surcharge_type') == 'per_unit':
                    per_unit_surcharges += cv.get('surcharge_amount', 0.0)
                elif cv.get('surcharge_type') == 'fixed':
                    qty = cv.get('qty_override', 0.0) or 1.0
                    fixed_surcharges += cv.get('surcharge_amount', 0.0) * qty

        unit_price = computed_qty * (rate + per_unit_surcharges) + fixed_surcharges
        return unit_price

    def _format_config_notes(self, dim_values, config_selections):
        """Generate a single consolidated note with all config details.

        Args:
            dim_values: dict of {field_code: value}
            config_selections: dict of {variable_id: option record}
        Returns:
            list with a single formatted string (or empty list)
        """
        self.ensure_one()
        lines = []
        for group in self.display_group_ids.sorted('sequence'):
            if group.note_format:
                fmt_ctx = dict(dim_values)
                for var in self.variable_ids.filtered(lambda v: v.display_group_id == group):
                    option = config_selections.get(var.id)
                    if option:
                        fmt_ctx[var.name.lower().replace(' ', '_')] = option.name
                        if option.qty_override:
                            fmt_ctx[var.name.lower().replace(' ', '_') + '_qty'] = int(option.qty_override)
                try:
                    line = group.note_format.format(**fmt_ctx)
                except (KeyError, ValueError):
                    line = self._build_group_note_fallback(group, dim_values, config_selections)
                if line:
                    lines.append(line)
            else:
                line = self._build_group_note_fallback(group, dim_values, config_selections)
                if line:
                    lines.append(line)
        return lines

    def _build_group_note_fallback(self, group, dim_values, config_selections):
        """Build a note line from group variables when no format template exists."""
        parts = []
        if group.show_dimensions:
            dim_parts = []
            for dim_line in self.dimension_line_ids.filtered(lambda d: d.show_on_quotation):
                val = dim_values.get(dim_line.field_code, 0)
                if val:
                    dim_parts.append(f"{int(val)}{dim_line.uom_type}")
            if dim_parts:
                dim_str = ' \u00d7 '.join(dim_parts)
                parts.append(dim_str)

        # Extra dimensions for this group
        for dim_line in group.extra_dimension_ids:
            val = dim_values.get(dim_line.field_code, 0)
            if val:
                parts.append(f"{dim_line.name}: {int(val)}{dim_line.uom_type}")

        # Variable selections
        for var in self.variable_ids.filtered(lambda v: v.display_group_id == group).sorted('sequence'):
            option = config_selections.get(var.id)
            if option:
                if option.qty_override and option.qty_override > 1:
                    parts.append(f"{var.name}: {option.name} \u00d7{int(option.qty_override)}")
                else:
                    parts.append(f"{var.name}: {option.name}")

        if parts:
            return f"{group.name}: {' | '.join(parts)}"
        return ''

    def action_view_products(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Products using {self.name}',
            'res_model': 'product.template',
            'view_mode': 'list,form',
            'domain': [('dimension_template_id', '=', self.id)],
        }
