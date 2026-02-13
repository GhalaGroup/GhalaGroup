# -*- coding: utf-8 -*-
import json
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    has_dimensions = fields.Boolean(string='Has Dimensions',
                                    related='product_template_id.has_dimensions')
    dimension_template_id = fields.Many2one('vpa.dimension.template', string='Dimension Template',
                                            related='product_template_id.dimension_template_id')
    dimension_value_ids = fields.One2many('sale.order.line.dimension', 'sale_line_id',
                                          string='Dimension Values')
    config_value_ids = fields.One2many('sale.order.line.config', 'sale_line_id',
                                       string='Configuration Values')
    computed_qty = fields.Float(string='Computed Qty', digits=(16, 4),
                                help='Computed area/volume from dimensions')
    computed_qty_display = fields.Char(string='Dim. Qty', compute='_compute_qty_display')
    config_summary = fields.Char(string='Config Summary', compute='_compute_config_summary')
    is_dimension_note = fields.Boolean(string='Is Dimension Note', default=False)
    dimension_parent_line_id = fields.Many2one('sale.order.line', string='Parent Configured Line',
                                               ondelete='cascade')
    dimension_note_line_ids = fields.One2many('sale.order.line', 'dimension_parent_line_id',
                                              string='Note Lines')
    dimension_data_json = fields.Text(string='Dimension Data (JSON)')

    @api.depends('computed_qty', 'dimension_template_id', 'has_dimensions')
    def _compute_qty_display(self):
        unit_labels = {'m2': 'm\u00b2', 'm3': 'm\u00b3', 'linear_m': 'm', 'custom': ''}
        for line in self:
            if line.computed_qty and line.dimension_template_id:
                label = unit_labels.get(line.dimension_template_id.calculation_type, '')
                line.computed_qty_display = f"{line.computed_qty:.2f} {label}"
            elif line.has_dimensions and not line.computed_qty:
                line.computed_qty_display = '\u2699 Configure...'
            else:
                line.computed_qty_display = ''

    @api.depends('dimension_value_ids', 'config_value_ids')
    def _compute_config_summary(self):
        for line in self:
            if not line.dimension_value_ids:
                line.config_summary = ''
                continue
            parts = []
            # Dimensions
            dim_parts = []
            for dv in line.dimension_value_ids:
                if dv.value:
                    dim_parts.append(f"{int(dv.value)}")
            if dim_parts:
                parts.append('\u00d7'.join(dim_parts) + 'mm')
            # Config selections
            for cv in line.config_value_ids:
                if cv.option_id:
                    parts.append(cv.option_id.name)
            line.config_summary = ' | '.join(parts) if parts else ''

    def action_open_configurator(self):
        """Open the product configurator popup for this SO line."""
        self.ensure_one()
        template = self.product_template_id.dimension_template_id
        if not template:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': f'Configure: {self.product_template_id.name}',
            'res_model': 'vpa.product.configurator.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_line_id': self.id,
                'default_product_id': self.product_id.id,
                'default_template_id': template.id,
            },
        }

    @api.depends('product_id', 'product_uom_id', 'product_uom_qty')
    def _compute_price_unit(self):
        """Override to apply dimension-based pricing for configured products."""
        super()._compute_price_unit()
        for line in self:
            if not line.has_dimensions or not line.computed_qty or not line.dimension_template_id:
                continue
            # Check for manual price edit
            if line.order_id and line.order_id.currency_id:
                if line.order_id.currency_id.compare_amounts(line.technical_price_unit, line.price_unit):
                    continue
            # Calculate dimension-based price
            template = line.dimension_template_id
            rate = line.product_template_id._get_dimension_rate()
            config_data = []
            for cv in line.config_value_ids:
                opt = cv.option_id
                if opt and opt.surcharge_type != 'none':
                    config_data.append({
                        'surcharge_type': opt.surcharge_type,
                        'surcharge_amount': opt.surcharge_amount,
                        'qty_override': opt.qty_override,
                    })
            dim_values = {}
            for dv in line.dimension_value_ids:
                dim_values[dv.dimension_line_id.field_code] = dv.value
            unit_price = template.evaluate_price(dim_values, rate, config_data)
            if unit_price > 0:
                line.price_unit = unit_price
                line.technical_price_unit = unit_price

    def _prepare_procurement_values(self):
        """Override to inject dimension data into procurement for MO creation."""
        values = super()._prepare_procurement_values()
        if self.has_dimensions and self.dimension_data_json:
            values['vpa_dimension_data'] = self.dimension_data_json
        return values

    def _serialize_dimension_data(self):
        """Serialize all dimension and config data to JSON for MO pass-through."""
        self.ensure_one()
        data = {
            'template_id': self.dimension_template_id.id,
            'template_name': self.dimension_template_id.name,
            'calculation_type': self.dimension_template_id.calculation_type,
            'computed_qty': self.computed_qty,
            'unit_count': self.product_uom_qty,
            'dimensions': {},
            'config': [],
            'display_groups': [],
        }
        for dv in self.dimension_value_ids:
            data['dimensions'][dv.dimension_line_id.field_code] = {
                'name': dv.dimension_line_id.name,
                'value': dv.value,
                'uom_type': dv.dimension_line_id.uom_type,
            }
        for cv in self.config_value_ids:
            cfg = {
                'variable_id': cv.variable_id.id,
                'variable_name': cv.variable_id.name,
                'variable_type': cv.variable_id.variable_type,
                'option_id': cv.option_id.id,
                'option_name': cv.option_id.name,
                'surcharge_type': cv.option_id.surcharge_type,
                'surcharge_amount': cv.option_id.surcharge_amount,
                'qty_override': cv.option_id.qty_override,
            }
            if cv.product_id:
                cfg['product_id'] = cv.product_id.id
                cfg['product_name'] = cv.product_id.name
            data['config'].append(cfg)
        # Display groups for MO spec panel
        for group in self.dimension_template_id.display_group_ids.sorted('sequence'):
            group_data = {
                'name': group.name,
                'show_dimensions': group.show_dimensions,
                'variables': [],
            }
            for var in self.dimension_template_id.variable_ids.filtered(
                lambda v: v.display_group_id == group
            ).sorted('sequence'):
                cv = self.config_value_ids.filtered(lambda c: c.variable_id == var)
                if cv:
                    group_data['variables'].append({
                        'name': var.name,
                        'value': cv.option_id.name,
                        'qty_override': cv.option_id.qty_override,
                    })
            # Extra dimensions
            for dim_line in group.extra_dimension_ids:
                dv = self.dimension_value_ids.filtered(lambda d: d.dimension_line_id == dim_line)
                if dv:
                    group_data['variables'].append({
                        'name': dim_line.name,
                        'value': f"{int(dv.value)}{dim_line.uom_type}",
                        'qty_override': 0,
                    })
            data['display_groups'].append(group_data)
        return json.dumps(data)

    def _generate_config_note_lines(self):
        """Create/update display-only note lines under this configured product line."""
        self.ensure_one()
        if not self.has_dimensions or not self.dimension_template_id:
            return
        # Delete existing note lines
        self._delete_config_note_lines()
        # Build dimension values dict
        dim_values = {}
        for dv in self.dimension_value_ids:
            dim_values[dv.dimension_line_id.field_code] = dv.value
        # Build config selections dict
        config_selections = {}
        for cv in self.config_value_ids:
            config_selections[cv.variable_id.id] = cv.option_id
        # Generate notes from template
        notes = self.dimension_template_id._format_config_notes(dim_values, config_selections)
        # Create note lines
        sequence = self.sequence
        for note_text in notes:
            if not note_text:
                continue
            sequence += 1
            self.env['sale.order.line'].create({
                'order_id': self.order_id.id,
                'display_type': 'line_note',
                'name': note_text,
                'sequence': sequence,
                'is_dimension_note': True,
                'dimension_parent_line_id': self.id,
                'product_id': False,
                'product_uom_qty': 0,
                'product_uom_id': False,
                'price_unit': 0,
                'customer_lead': 0,
            })

    def _delete_config_note_lines(self):
        """Remove auto-generated note lines for this configured product."""
        self.ensure_one()
        self.dimension_note_line_ids.unlink()

    def unlink(self):
        """Override to cascade-delete dimension note lines."""
        note_lines = self.env['sale.order.line']
        for line in self:
            note_lines |= line.dimension_note_line_ids
        if note_lines:
            note_lines.unlink()
        return super().unlink()
