# -*- coding: utf-8 -*-
import base64
import io
from odoo import api, fields, models, _
from odoo.exceptions import UserError

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class VpaDimensionImportWizard(models.TransientModel):
    _name = 'vpa.dimension.import.wizard'
    _description = 'Dimension Import Wizard'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    state = fields.Selection([
        ('upload', 'Upload'),
        ('preview', 'Preview'),
        ('done', 'Done'),
    ], default='upload')

    file_data = fields.Binary(string='Excel File', attachment=False)
    file_name = fields.Char(string='File Name')
    template_id = fields.Many2one('vpa.dimension.template', string='Template',
                                   help='Template for download. Leave empty to include all templates.')

    preview_html = fields.Html(string='Preview', sanitize=False, readonly=True)
    import_count = fields.Integer(string='Lines to Import', readonly=True)
    preview_data_json = fields.Text(string='Preview Data')

    def action_download_template(self):
        """Download an Excel template with proper column headers."""
        if not xlsxwriter:
            raise UserError(_("xlsxwriter is not installed. Please install it to use this feature."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        templates = self.template_id or self.env['vpa.dimension.template'].search([('active', '=', True)])

        for template in templates:
            sheet_name = (template.code or template.name)[:31]
            worksheet = workbook.add_worksheet(sheet_name)

            # Headers
            header_format = workbook.add_format({'bold': True, 'bg_color': '#875A7B', 'font_color': 'white'})
            col = 0
            worksheet.write(0, col, 'Product Code', header_format)
            col += 1
            worksheet.write(0, col, 'Quantity', header_format)
            col += 1

            # Dimension columns
            for dim_line in template.dimension_line_ids.sorted('sequence'):
                worksheet.write(0, col, f"{dim_line.name} ({dim_line.uom_type})", header_format)
                col += 1

            # Variable columns
            for var in template.variable_ids.sorted('sequence'):
                header_text = var.name
                if var.option_ids:
                    options = ', '.join(var.option_ids.mapped('name'))
                    header_text = f"{var.name} [{options}]"
                worksheet.write(0, col, header_text, header_format)
                col += 1

            # Auto-width
            for c in range(col):
                worksheet.set_column(c, c, 18)

        workbook.close()
        output.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': 'Dimension_Import_Template.xlsx',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    def action_preview(self):
        """Parse uploaded Excel and show preview."""
        self.ensure_one()
        if not self.file_data:
            raise UserError(_("Please upload an Excel file."))
        if not openpyxl:
            raise UserError(_("openpyxl is not installed. Please install it to use this feature."))

        file_content = base64.b64decode(self.file_data)
        workbook = openpyxl.load_workbook(io.BytesIO(file_content), read_only=True)

        lines = []
        errors = []

        for sheet in workbook.sheetnames:
            ws = workbook[sheet]
            headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
            if not headers or headers[0] is None:
                continue

            for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not row or not row[0]:
                    continue
                product_code = str(row[0]).strip()
                qty = float(row[1] or 1) if len(row) > 1 else 1

                # Find product
                product = self.env['product.product'].search([
                    '|', ('default_code', '=', product_code),
                    ('name', '=', product_code),
                ], limit=1)

                if not product:
                    errors.append(f"Row {row_idx}: Product '{product_code}' not found")
                    continue

                template = product.product_tmpl_id.dimension_template_id
                if not template:
                    errors.append(f"Row {row_idx}: Product '{product_code}' has no dimension template")
                    continue

                # Parse dimensions
                dim_values = {}
                col = 2
                for dim_line in template.dimension_line_ids.sorted('sequence'):
                    if col < len(row) and row[col] is not None:
                        try:
                            dim_values[dim_line.field_code] = float(row[col])
                        except (ValueError, TypeError):
                            errors.append(f"Row {row_idx}: Invalid value for {dim_line.name}")
                    col += 1

                # Parse config
                config_selections = {}
                for var in template.variable_ids.sorted('sequence'):
                    if col < len(row) and row[col] is not None:
                        option_name = str(row[col]).strip()
                        option = var.option_ids.filtered(
                            lambda o: o.name.lower() == option_name.lower()
                        )[:1]
                        if option:
                            config_selections[var.id] = option
                        elif option_name:
                            errors.append(
                                f"Row {row_idx}: Unknown option '{option_name}' for {var.name}"
                            )
                    col += 1

                # Calculate price
                rate = product.product_tmpl_id._get_dimension_rate()
                config_data = []
                for var_id, opt in config_selections.items():
                    if opt.surcharge_type != 'none':
                        config_data.append({
                            'surcharge_type': opt.surcharge_type,
                            'surcharge_amount': opt.surcharge_amount,
                            'qty_override': opt.qty_override,
                        })
                computed_qty = template.evaluate_quantity(dim_values)
                unit_price = template.evaluate_price(dim_values, rate, config_data)

                lines.append({
                    'product_id': product.id,
                    'product_name': product.display_name,
                    'qty': qty,
                    'dim_values': dim_values,
                    'config_selections': {k: v.id for k, v in config_selections.items()},
                    'computed_qty': computed_qty,
                    'unit_price': unit_price,
                })

        # Build preview HTML
        html = '<table class="table table-sm table-bordered">'
        html += '<thead><tr><th>Product</th><th>Qty</th><th>Dimensions</th><th>Unit Price</th></tr></thead>'
        html += '<tbody>'
        for line in lines:
            dims = ' \u00d7 '.join(f"{int(v)}" for v in line['dim_values'].values())
            html += f"<tr><td>{line['product_name']}</td><td>{line['qty']}</td>"
            html += f"<td>{dims}</td><td>{line['unit_price']:.2f}</td></tr>"
        html += '</tbody></table>'

        if errors:
            html += '<div class="alert alert-warning mt-2"><strong>Warnings:</strong><ul>'
            for err in errors:
                html += f'<li>{err}</li>'
            html += '</ul></div>'

        import json
        self.write({
            'state': 'preview',
            'preview_html': html,
            'import_count': len(lines),
            'preview_data_json': json.dumps(lines),
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import(self):
        """Create SO lines from preview data."""
        self.ensure_one()
        if not self.preview_data_json:
            raise UserError(_("No data to import. Please preview first."))

        import json
        lines_data = json.loads(self.preview_data_json)
        order = self.sale_order_id

        for line_data in lines_data:
            product = self.env['product.product'].browse(line_data['product_id'])
            template = product.product_tmpl_id.dimension_template_id

            # Create SO line
            sol = self.env['sale.order.line'].create({
                'order_id': order.id,
                'product_id': product.id,
                'product_uom_qty': line_data['qty'],
                'price_unit': line_data['unit_price'],
                'technical_price_unit': line_data['unit_price'],
            })

            # Write dimension values
            dim_vals = []
            for dim_line in template.dimension_line_ids:
                val = line_data['dim_values'].get(dim_line.field_code, 0)
                if val:
                    dim_vals.append((0, 0, {
                        'dimension_line_id': dim_line.id,
                        'value': val,
                    }))
            sol.dimension_value_ids = dim_vals

            # Write config values
            config_vals = []
            for var_id_str, option_id in line_data.get('config_selections', {}).items():
                var_id = int(var_id_str)
                config_vals.append((0, 0, {
                    'variable_id': var_id,
                    'option_id': option_id,
                }))
            sol.config_value_ids = config_vals

            # Set computed qty and serialize
            sol.computed_qty = line_data['computed_qty']

            # Build name
            dim_parts = [f"{int(v)}" for v in line_data['dim_values'].values()]
            if dim_parts:
                sol.name = f"{product.name} - {'\u00d7'.join(dim_parts)}mm"

            sol.dimension_data_json = sol._serialize_dimension_data()
            sol._generate_config_note_lines()

        self.state = 'done'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': order.id,
            'view_mode': 'form',
            'target': 'current',
        }
