# -*- coding: utf-8 -*-
import json
from markupsafe import Markup
from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    dimension_template_id = fields.Many2one('vpa.dimension.template', string='Dimension Template')
    dimension_data_json = fields.Text(string='Dimension Data (JSON)')
    computed_dimension_qty = fields.Float(string='Computed Qty (per unit)', digits=(16, 4),
                                          help='Area/volume per single unit')
    dimension_unit_count = fields.Integer(string='Unit Count',
                                          help='Number of units (e.g., 5 doors)')
    dimension_display = fields.Html(string='Production Specifications',
                                    compute='_compute_dimension_display', sanitize=False)
    has_dimension_data = fields.Boolean(string='Has Dimension Data',
                                        compute='_compute_has_dimension_data')

    @api.depends('dimension_data_json')
    def _compute_has_dimension_data(self):
        for rec in self:
            rec.has_dimension_data = bool(rec.dimension_data_json)

    @api.depends('dimension_data_json')
    def _compute_dimension_display(self):
        for rec in self:
            if not rec.dimension_data_json:
                rec.dimension_display = ''
                continue
            try:
                data = json.loads(rec.dimension_data_json)
            except (json.JSONDecodeError, TypeError):
                rec.dimension_display = ''
                continue
            rec.dimension_display = Markup(rec._build_spec_html(data))

    def _build_spec_html(self, data):
        """Build a compact HTML specification table from dimension data."""
        unit_count = data.get('unit_count', 1)
        dims = data.get('dimensions', {})
        calc_type = data.get('calculation_type', 'm2')
        unit_labels = {'m2': 'm\u00b2', 'm3': 'm\u00b3', 'linear_m': 'm', 'custom': ''}
        unit_label = unit_labels.get(calc_type, '')
        computed_qty = data.get('computed_qty', 0)
        total_qty = computed_qty * unit_count

        # Collect all rows: (label, value)
        rows = []

        # Quantity row (only if > 1)
        if unit_count > 1:
            rows.append(('Quantity', f'{int(unit_count)} units'))

        # Size row — e.g. "900 x 2100 mm"
        if dims:
            dim_parts = []
            for code, dim_info in dims.items():
                dim_parts.append(str(int(dim_info.get('value', 0))))
            uom = list(dims.values())[0].get('uom_type', 'mm') if dims else 'mm'
            rows.append(('Size', f'{" \u00d7 ".join(dim_parts)} {uom}'))

        # Area/volume row
        if computed_qty:
            if unit_count > 1:
                rows.append(('Area', f'{computed_qty:.2f} {unit_label} per unit / {total_qty:.2f} {unit_label} total'))
            else:
                rows.append(('Area', f'{computed_qty:.2f} {unit_label}'))

        # Display group variables
        for group in data.get('display_groups', []):
            variables = group.get('variables', [])
            if group.get('show_dimensions') and not variables:
                continue
            for var in variables:
                var_name = var.get('name', '')
                var_value = var.get('value', '')
                qty = var.get('qty_override', 0)
                if qty and qty > 1:
                    rows.append((var_name, f'{var_value} \u00d7{int(qty)}'))
                else:
                    rows.append((var_name, var_value))

        if not rows:
            return ''

        # Build compact table
        html = (
            '<table style="border-collapse:collapse; font-size:13px; width:auto; '
            'max-width:500px; margin:4px 0;">'
        )
        for label, value in rows:
            html += (
                f'<tr>'
                f'<td style="padding:3px 12px 3px 0; color:#888; white-space:nowrap; '
                f'vertical-align:top;">{label}</td>'
                f'<td style="padding:3px 0; font-weight:600;">{value}</td>'
                f'</tr>'
            )
        html += '</table>'
        return html

    def _get_moves_raw_values(self):
        """Override to apply dimension scaling and product replacement."""
        moves = super()._get_moves_raw_values()
        if not self.has_dimension_data or not self.dimension_data_json:
            return moves

        try:
            data = json.loads(self.dimension_data_json)
        except (json.JSONDecodeError, TypeError):
            return moves

        computed_qty = data.get('computed_qty', 0)
        unit_count = data.get('unit_count', 1)
        total_qty = computed_qty * unit_count

        # Build config lookup: {variable_id: config_entry}
        config_lookup = {}
        for cfg in data.get('config', []):
            config_lookup[cfg.get('variable_id')] = cfg

        updated_moves = []
        for move_vals in moves:
            bom_line_id = move_vals.get('bom_line_id')
            if not bom_line_id:
                updated_moves.append(move_vals)
                continue

            bom_line = self.env['mrp.bom.line'].browse(bom_line_id)

            # Scale with dimensions
            if bom_line.scales_with_dimensions and total_qty:
                move_vals['product_uom_qty'] = move_vals.get('product_uom_qty', 0) * total_qty

            # Replace placeholder with user's selected product
            if bom_line.linked_variable_id:
                var_id = bom_line.linked_variable_id.id
                cfg = config_lookup.get(var_id)
                if cfg and cfg.get('product_id'):
                    product = self.env['product.product'].browse(cfg['product_id'])
                    if product.exists():
                        move_vals['product_id'] = product.id
                        move_vals['name'] = product.display_name
                        # Apply qty override
                        qty_override = cfg.get('qty_override', 0)
                        if qty_override:
                            move_vals['product_uom_qty'] = qty_override * unit_count
                        # Update UoM if different
                        if product.uom_id:
                            move_vals['product_uom_id'] = product.uom_id.id

            updated_moves.append(move_vals)
        return updated_moves
