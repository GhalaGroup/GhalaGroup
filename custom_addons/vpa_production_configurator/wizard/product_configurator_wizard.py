# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class VpaProductConfiguratorWizard(models.TransientModel):
    _name = 'vpa.product.configurator.wizard'
    _description = 'Product Configurator Wizard'

    sale_line_id = fields.Many2one('sale.order.line', string='Sale Line', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    template_id = fields.Many2one('vpa.dimension.template', string='Template', required=True)
    rate = fields.Float(string='Rate', digits='Product Price')

    dimension_line_ids = fields.One2many('vpa.configurator.dimension.line', 'wizard_id',
                                         string='Dimensions')
    config_line_ids = fields.One2many('vpa.configurator.config.line', 'wizard_id',
                                      string='Configuration')

    preview_qty = fields.Float(string='Computed Quantity', digits=(16, 4))
    preview_qty_label = fields.Char(string='Qty Label')
    preview_base_price = fields.Float(string='Base Price', digits='Product Price')
    preview_surcharges_display = fields.Text(string='Surcharges')
    preview_total_price = fields.Float(string='Unit Price', digits='Product Price')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        sale_line_id = res.get('sale_line_id') or self.env.context.get('default_sale_line_id')
        if sale_line_id:
            sale_line = self.env['sale.order.line'].browse(sale_line_id)
            product = sale_line.product_id
            template = product.product_tmpl_id.dimension_template_id
            if template:
                res['template_id'] = template.id
                res['product_id'] = product.id
                rate = product.product_tmpl_id._get_dimension_rate()
                res['rate'] = rate

                # Populate dimension lines
                dim_lines = []
                dim_values = {}
                existing_dims = {dv.dimension_line_id.id: dv.value
                                 for dv in sale_line.dimension_value_ids}
                for dim_line in template.dimension_line_ids.sorted('sequence'):
                    value = existing_dims.get(dim_line.id, dim_line.default_value or 0)
                    dim_lines.append((0, 0, {
                        'dimension_line_id': dim_line.id,
                        'value': value,
                    }))
                    dim_values[dim_line.field_code] = value
                res['dimension_line_ids'] = dim_lines

                # Populate config lines
                config_lines = []
                existing_config = {cv.variable_id.id: cv.option_id.id
                                   for cv in sale_line.config_value_ids}
                option_records = {}
                for var in template.variable_ids.sorted('sequence'):
                    default_option = False
                    if var.id in existing_config:
                        default_option = existing_config[var.id]
                    else:
                        default_opt = var.option_ids.filtered('is_default')[:1]
                        if default_opt:
                            default_option = default_opt.id
                    config_lines.append((0, 0, {
                        'variable_id': var.id,
                        'option_id': default_option,
                    }))
                    if default_option:
                        opt = self.env['vpa.config.variable.option'].browse(default_option)
                        option_records[var.name] = opt
                res['config_line_ids'] = config_lines

                # Pre-compute the preview since @api.onchange won't fire on initial load
                preview = self._calculate_preview(template, dim_values, rate, option_records)
                res.update(preview)
        return res

    def _calculate_preview(self, template, dim_values, rate, option_records=None):
        """Calculate preview values. Returns dict of preview field values.

        Args:
            template: vpa.dimension.template record
            dim_values: dict of {field_code: value}
            rate: base rate per unit
            option_records: dict of {var_name: option_record} for surcharges
        """
        unit_labels = {'m2': 'm\u00b2', 'm3': 'm\u00b3', 'linear_m': 'm', 'custom': ''}
        result = {
            'preview_qty': 0,
            'preview_qty_label': unit_labels.get(template.calculation_type, ''),
            'preview_base_price': 0,
            'preview_surcharges_display': '',
            'preview_total_price': 0,
        }

        if not dim_values:
            return result

        computed_qty = template.evaluate_quantity(dim_values)
        result['preview_qty'] = computed_qty
        result['preview_base_price'] = computed_qty * rate

        per_unit_total = 0
        fixed_total = 0
        surcharge_lines = []
        if option_records:
            for var_name, opt in option_records.items():
                if opt.surcharge_type == 'per_unit':
                    amount = opt.surcharge_amount * computed_qty
                    per_unit_total += opt.surcharge_amount
                    surcharge_lines.append(
                        f"{var_name}: +{opt.surcharge_amount:,.2f}{result['preview_qty_label']} "
                        f"\u00d7 {computed_qty:.4f} = +{amount:,.2f}"
                    )
                elif opt.surcharge_type == 'fixed':
                    qty = opt.qty_override or 1
                    amount = opt.surcharge_amount * qty
                    fixed_total += amount
                    if qty > 1:
                        surcharge_lines.append(
                            f"{var_name}: +{opt.surcharge_amount:,.2f} \u00d7 {int(qty)}pcs = +{amount:,.2f}"
                        )
                    else:
                        surcharge_lines.append(f"{var_name}: +{amount:,.2f}")

        result['preview_surcharges_display'] = '\n'.join(surcharge_lines) if surcharge_lines else ''
        result['preview_total_price'] = computed_qty * (rate + per_unit_total) + fixed_total
        return result

    @api.onchange('dimension_line_ids', 'config_line_ids', 'rate')
    def _onchange_recompute_preview(self):
        """Recompute the price preview whenever dimensions or config change."""
        if not self.template_id:
            return

        dim_values = {}
        for dl in self.dimension_line_ids:
            if dl.field_code:
                dim_values[dl.field_code] = dl.value or 0

        option_records = {}
        for cl in self.config_line_ids:
            if cl.option_id:
                option_records[cl.name] = cl.option_id

        preview = self._calculate_preview(self.template_id, dim_values, self.rate or 0, option_records)
        self.preview_qty = preview['preview_qty']
        self.preview_qty_label = preview['preview_qty_label']
        self.preview_base_price = preview['preview_base_price']
        self.preview_surcharges_display = preview['preview_surcharges_display']
        self.preview_total_price = preview['preview_total_price']

    def action_apply(self):
        """Apply configuration to the sale order line."""
        self.ensure_one()
        sale_line = self.sale_line_id

        # Validate required dimensions
        for dl in self.dimension_line_ids:
            if dl.required and not dl.value:
                raise UserError(_("Dimension '%s' is required.", dl.name))
            if dl.min_value and dl.value < dl.min_value:
                raise UserError(
                    _("%(name)s must be at least %(min)s%(uom)s.",
                      name=dl.name, min=dl.min_value, uom=dl.uom_type)
                )
            if dl.max_value and dl.value > dl.max_value:
                raise UserError(
                    _("%(name)s must be at most %(max)s%(uom)s.",
                      name=dl.name, max=dl.max_value, uom=dl.uom_type)
                )

        # Validate required config
        for cl in self.config_line_ids:
            if cl.required and not cl.option_id:
                raise UserError(_("Configuration '%s' is required.", cl.name))

        # Write dimension values
        sale_line.dimension_value_ids.unlink()
        dim_vals = []
        for dl in self.dimension_line_ids:
            dim_vals.append((0, 0, {
                'dimension_line_id': dl.dimension_line_id.id,
                'value': dl.value,
            }))
        sale_line.dimension_value_ids = dim_vals

        # Write config values
        sale_line.config_value_ids.unlink()
        config_vals = []
        for cl in self.config_line_ids:
            if cl.option_id:
                config_vals.append((0, 0, {
                    'variable_id': cl.variable_id.id,
                    'option_id': cl.option_id.id,
                }))
        sale_line.config_value_ids = config_vals

        # Compute area/volume and price
        dim_values = {}
        for dl in self.dimension_line_ids:
            dim_values[dl.field_code] = dl.value
        option_records = {}
        for cl in self.config_line_ids:
            if cl.option_id:
                option_records[cl.name] = cl.option_id
        preview = self._calculate_preview(
            self.template_id, dim_values, self.rate or 0, option_records
        )
        computed_qty = preview['preview_qty']
        total_price = preview['preview_total_price']
        sale_line.computed_qty = computed_qty

        # Build dimension summary for SO line name
        dim_parts = []
        for dl in self.dimension_line_ids:
            if dl.value and dl.dimension_line_id.show_on_quotation:
                dim_parts.append(f"{int(dl.value)}")
        dim_summary = '\u00d7'.join(dim_parts) + 'mm' if dim_parts else ''
        if dim_summary:
            base_name = self.product_id.name
            sale_line.name = f"{base_name} - {dim_summary}"

        # Set price
        sale_line.price_unit = total_price
        sale_line.technical_price_unit = total_price

        # Serialize dimension data for MO pass-through
        sale_line.dimension_data_json = sale_line._serialize_dimension_data()

        # Generate note lines for quotation display
        sale_line._generate_config_note_lines()

        return {'type': 'ir.actions.act_window_close'}


class VpaConfiguratorDimensionLine(models.TransientModel):
    _name = 'vpa.configurator.dimension.line'
    _description = 'Configurator Dimension Line'
    _order = 'sequence, id'

    wizard_id = fields.Many2one('vpa.product.configurator.wizard', ondelete='cascade')
    dimension_line_id = fields.Many2one('vpa.dimension.template.line', string='Dimension')
    name = fields.Char(string='Label', related='dimension_line_id.name', readonly=True)
    field_code = fields.Char(string='Code', related='dimension_line_id.field_code', readonly=True)
    uom_type = fields.Selection(related='dimension_line_id.uom_type', string='Unit', readonly=True)
    value = fields.Float(string='Value')
    min_value = fields.Float(string='Min', related='dimension_line_id.min_value', readonly=True)
    max_value = fields.Float(string='Max', related='dimension_line_id.max_value', readonly=True)
    required = fields.Boolean(string='Required', related='dimension_line_id.required', readonly=True)
    sequence = fields.Integer(string='Sequence', related='dimension_line_id.sequence', readonly=True)


class VpaConfiguratorConfigLine(models.TransientModel):
    _name = 'vpa.configurator.config.line'
    _description = 'Configurator Config Line'
    _order = 'sequence, id'

    wizard_id = fields.Many2one('vpa.product.configurator.wizard', ondelete='cascade')
    variable_id = fields.Many2one('vpa.config.variable', string='Variable')
    name = fields.Char(string='Label', related='variable_id.name', readonly=True)
    variable_type = fields.Selection(related='variable_id.variable_type', string='Type', readonly=True)
    display_group_name = fields.Char(string='Group', related='variable_id.display_group_id.name', readonly=True)
    required = fields.Boolean(string='Required', related='variable_id.required', readonly=True)
    affects_price = fields.Boolean(string='Affects Price', related='variable_id.affects_price', readonly=True)
    option_id = fields.Many2one('vpa.config.variable.option', string='Selection',
                                domain="[('variable_id', '=', variable_id)]")
    surcharge_display = fields.Char(string='Surcharge', compute='_compute_surcharge_display')
    sequence = fields.Integer(string='Sequence', related='variable_id.sequence', readonly=True)

    @api.depends('option_id')
    def _compute_surcharge_display(self):
        unit_labels = {'m2': '/m\u00b2', 'm3': '/m\u00b3', 'linear_m': '/m', 'custom': ''}
        for line in self:
            if not line.option_id or line.option_id.surcharge_type == 'none':
                line.surcharge_display = ''
                continue
            opt = line.option_id
            if opt.surcharge_type == 'per_unit':
                template = line.wizard_id.template_id
                label = unit_labels.get(template.calculation_type, '') if template else ''
                line.surcharge_display = f"+{opt.surcharge_amount:,.2f}{label}"
            elif opt.surcharge_type == 'fixed':
                qty = opt.qty_override or 1
                if qty > 1:
                    line.surcharge_display = f"+{opt.surcharge_amount:,.2f} \u00d7{int(qty)}pcs"
                else:
                    line.surcharge_display = f"+{opt.surcharge_amount:,.2f}"
