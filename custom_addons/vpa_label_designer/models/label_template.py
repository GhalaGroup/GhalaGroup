# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

import base64
import json
import logging
import re
from datetime import date

import requests

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class LabelTemplate(models.Model):
    _name = 'vpa.label.template'
    _description = 'Label Template'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(string='Template Name', required=True, tracking=True)
    label_size_id = fields.Many2one('vpa.label.size', string='Label Size',
                                    required=True, tracking=True)
    model_name = fields.Selection([
        ('product.product', 'Product'),
        ('stock.picking', 'Stock Picking / Transfer'),
        ('stock.lot', 'Lot / Serial Number'),
        ('mrp.production', 'Manufacturing Order'),
        ('purchase.order', 'Purchase Order'),
    ], string='Source Model', required=True, default='product.product', tracking=True)

    element_ids = fields.One2many('vpa.label.element', 'template_id',
                                  string='Label Elements')

    # RFID
    has_rfid = fields.Boolean(related='label_size_id.has_rfid', string='RFID Label')
    rfid_data_variable_id = fields.Many2one('vpa.label.variable',
                                            string='RFID Data Variable',
                                            help='Variable to encode into RFID tag (EPC Gen2)')

    # Computed ZPL
    zpl_code = fields.Text(string='ZPL Code', compute='_compute_zpl_code')
    zpl_preview = fields.Text(string='ZPL Preview', compute='_compute_zpl_preview')

    # Preview
    preview_image = fields.Binary(string='Preview Image', attachment=False)

    # Label dimensions for preview (in inches and dpmm for Labelary API)
    label_width_inch = fields.Float(compute='_compute_label_dimensions')
    label_height_inch = fields.Float(compute='_compute_label_dimensions')
    label_dpmm = fields.Integer(compute='_compute_label_dimensions')

    # Label dimensions for canvas editor (in dots and DPI)
    label_width_dots = fields.Integer(related='label_size_id.width_dots', string='Label Width (dots)')
    label_height_dots = fields.Integer(related='label_size_id.height_dots', string='Label Height (dots)')
    label_dpi = fields.Integer(compute='_compute_label_dpi', string='Label DPI')

    is_default = fields.Boolean(
        string='Default Template',
        help='When checked, this template is used by default when printing '
             'labels for the selected Source Model.')

    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    def write(self, vals):
        res = super().write(vals)
        if vals.get('is_default'):
            # Unset other defaults for same model_name + company
            for rec in self:
                others = self.search([
                    ('id', '!=', rec.id),
                    ('model_name', '=', rec.model_name),
                    ('company_id', 'in', [False, rec.company_id.id]),
                    ('is_default', '=', True),
                ])
                if others:
                    others.write({'is_default': False})
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.is_default:
                others = self.search([
                    ('id', '!=', rec.id),
                    ('model_name', '=', rec.model_name),
                    ('company_id', 'in', [False, rec.company_id.id]),
                    ('is_default', '=', True),
                ])
                if others:
                    others.write({'is_default': False})
        return records

    @api.depends('label_size_id', 'label_size_id.dpi')
    def _compute_label_dpi(self):
        """Get integer DPI from label size."""
        for rec in self:
            rec.label_dpi = int(rec.label_size_id.dpi) if rec.label_size_id and rec.label_size_id.dpi else 203

    @api.depends('label_size_id', 'label_size_id.width_mm', 'label_size_id.height_mm',
                 'label_size_id.dpi')
    def _compute_label_dimensions(self):
        """Compute label dimensions in inches and dpmm for Labelary API."""
        for rec in self:
            if rec.label_size_id:
                rec.label_width_inch = round(rec.label_size_id.width_mm / 25.4, 2)
                rec.label_height_inch = round(rec.label_size_id.height_mm / 25.4, 2)
                dpi = int(rec.label_size_id.dpi) if rec.label_size_id.dpi else 203
                rec.label_dpmm = {203: 8, 300: 12, 600: 24}.get(dpi, 8)
            else:
                rec.label_width_inch = 4.0
                rec.label_height_inch = 2.0
                rec.label_dpmm = 8

    @api.depends('label_size_id', 'label_size_id.width_dots', 'label_size_id.height_dots',
                 'label_size_id.dpi', 'element_ids', 'element_ids.zpl_snippet',
                 'rfid_data_variable_id', 'label_size_id.has_rfid')
    def _compute_zpl_code(self):
        for rec in self:
            if not rec.label_size_id:
                rec.zpl_code = ''
                continue

            lines = []
            lines.append('^XA')  # Start label
            lines.append('^CI28')  # UTF-8 encoding
            lines.append(f'^PW{rec.label_size_id.width_dots}')  # Print width
            lines.append(f'^LL{rec.label_size_id.height_dots}')  # Label length

            # Add each element's ZPL
            for element in rec.element_ids.sorted('sequence'):
                if element.zpl_snippet:
                    lines.append(element.zpl_snippet)

            # RFID encoding
            if rec.label_size_id.has_rfid and rec.rfid_data_variable_id:
                var_name = rec.rfid_data_variable_id.name
                lines.append(f'^RFW,H^FD{{{{{var_name}}}}}^FS')  # Write RFID EPC

            lines.append('^XZ')  # End label

            rec.zpl_code = '\n'.join(lines)

    @api.depends('zpl_code')
    def _compute_zpl_preview(self):
        """Generate ZPL with sample values substituted for preview."""
        for rec in self:
            if not rec.zpl_code:
                rec.zpl_preview = ''
                continue

            zpl = rec.zpl_code
            # Find all {{VARIABLE_NAME}} placeholders
            variables = re.findall(r'\{\{(\w+)\}\}', zpl)
            if variables:
                var_records = self.env['vpa.label.variable'].search([
                    ('name', 'in', list(set(variables))),
                ])
                var_map = {v.name: v.sample_value or v.name for v in var_records}
                for var_name in variables:
                    zpl = zpl.replace('{{%s}}' % var_name, var_map.get(var_name, var_name))

            rec.zpl_preview = zpl

    def resolve_zpl_for_record(self, record, extra_values=None):
        """Resolve all variable placeholders against a specific Odoo record.

        Args:
            record: The Odoo record to resolve against
            extra_values: Optional dict of extra variable values (e.g., alt UoM data)

        Returns:
            str: ZPL code with all variables resolved
        """
        self.ensure_one()
        if not self.zpl_code:
            return ''

        zpl = self.zpl_code

        # Handle special variables
        special_values = {
            'PRINT_DATE': str(date.today()),
            'COMPANY_NAME': self.env.company.name or '',
            'COMPANY_PHONE': self.env.company.phone or '',
            'COMPANY_WEBSITE': self.env.company.website or '',
        }
        if extra_values:
            special_values.update(extra_values)

        # Find all variable placeholders
        variables = re.findall(r'\{\{(\w+)\}\}', zpl)
        if not variables:
            return zpl

        # Load variable definitions
        var_records = self.env['vpa.label.variable'].search([
            ('name', 'in', list(set(variables))),
        ])
        var_map = {v.name: v for v in var_records}

        # Resolve each variable
        for var_name in set(variables):
            if var_name in special_values:
                value = str(special_values[var_name])
            elif var_name in var_map:
                value = var_map[var_name].resolve_value(record, extra_values)
            else:
                value = ''

            zpl = zpl.replace('{{%s}}' % var_name, value)

        return zpl

    def resolve_zpl_for_records(self, records, extra_values_per_record=None):
        """Resolve ZPL for multiple records, generating one label per record.

        Args:
            records: Recordset of source records
            extra_values_per_record: Optional dict mapping record.id to extra_values dict

        Returns:
            str: Combined ZPL for all records
        """
        self.ensure_one()
        zpl_list = []
        for record in records:
            extra = (extra_values_per_record or {}).get(record.id, None)
            zpl_list.append(self.resolve_zpl_for_record(record, extra))
        return '\n'.join(zpl_list)

    def action_generate_preview(self):
        """Generate a visual preview of the label via Labelary API."""
        self.ensure_one()
        zpl = self.zpl_preview
        if not zpl:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Preview',
                    'message': 'No ZPL code to preview. Add some label elements first.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        try:
            url = f'http://api.labelary.com/v1/printers/{self.label_dpmm}dpmm/labels/{self.label_width_inch}x{self.label_height_inch}/0/'
            response = requests.post(
                url,
                data=zpl.encode('utf-8'),
                headers={'Accept': 'image/png'},
                timeout=15,
            )

            if response.status_code == 200:
                self.preview_image = base64.b64encode(response.content)
            else:
                _logger.warning('Labelary API returned status %s', response.status_code)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Preview Error',
                        'message': f'Labelary API returned status {response.status_code}',
                        'type': 'danger',
                        'sticky': False,
                    }
                }
        except requests.Timeout:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Preview Error',
                    'message': 'Labelary API request timed out. Please try again.',
                    'type': 'danger',
                    'sticky': False,
                }
            }
        except Exception as e:
            _logger.exception('Error generating label preview')
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Preview Error',
                    'message': str(e),
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def action_download_pdf(self):
        """Generate a PDF of the label via Labelary API and trigger download."""
        self.ensure_one()
        zpl = self.zpl_preview
        if not zpl:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'PDF Export',
                    'message': 'No ZPL code to export. Add some label elements first.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        try:
            url = f'http://api.labelary.com/v1/printers/{self.label_dpmm}dpmm/labels/{self.label_width_inch}x{self.label_height_inch}/0/'
            response = requests.post(
                url,
                data=zpl.encode('utf-8'),
                headers={'Accept': 'application/pdf'},
                timeout=15,
            )

            if response.status_code == 200:
                pdf_b64 = base64.b64encode(response.content)
                # Create an ir.attachment for download
                filename = f'{self.name or "label"}.pdf'
                attachment = self.env['ir.attachment'].create({
                    'name': filename,
                    'type': 'binary',
                    'datas': pdf_b64,
                    'mimetype': 'application/pdf',
                })
                return {
                    'type': 'ir.actions.act_url',
                    'url': f'/web/content/{attachment.id}?download=true',
                    'target': 'new',
                }
            else:
                _logger.warning('Labelary API returned status %s for PDF', response.status_code)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'PDF Error',
                        'message': f'Labelary API returned status {response.status_code}',
                        'type': 'danger',
                        'sticky': False,
                    }
                }
        except requests.Timeout:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'PDF Error',
                    'message': 'Labelary API request timed out. Please try again.',
                    'type': 'danger',
                    'sticky': False,
                }
            }
        except Exception as e:
            _logger.exception('Error generating label PDF')
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'PDF Error',
                    'message': str(e),
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def action_copy_zpl(self):
        """Return ZPL code for copy action (used by JS)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'ZPL Code',
                'message': 'ZPL code is available in the ZPL Code tab.',
                'type': 'info',
                'sticky': False,
            }
        }

    def action_export_template(self):
        """Export this template as a JSON file for backup/restore."""
        self.ensure_one()

        # Serialize label size
        size = self.label_size_id
        size_data = {
            'name': size.name,
            'width_mm': size.width_mm,
            'height_mm': size.height_mm,
            'dpi': size.dpi,
            'has_rfid': size.has_rfid,
            'rfid_position': size.rfid_position,
        }

        # Serialize elements
        elements = []
        for el in self.element_ids.sorted('sequence'):
            el_data = {
                'sequence': el.sequence,
                'name': el.name,
                'element_type': el.element_type,
                'pos_x': el.pos_x,
                'pos_y': el.pos_y,
                'content': el.content,
                'font_id': el.font_id,
                'font_height': el.font_height,
                'font_width': el.font_width,
                'rotation': el.rotation,
                'max_width': el.max_width,
                'max_lines': el.max_lines,
                'text_alignment': el.text_alignment,
                # Variable reference by name (portable across instances)
                'variable_name': el.variable_id.name if el.variable_id else False,
                # Barcode
                'barcode_type': el.barcode_type,
                'barcode_height': el.barcode_height,
                'barcode_module_width': el.barcode_module_width,
                'show_text_below': el.show_text_below,
                # QR Code
                'qr_magnification': el.qr_magnification,
                'qr_error_correction': el.qr_error_correction,
                # Shape
                'shape_width': el.shape_width,
                'shape_height': el.shape_height,
                'border_thickness': el.border_thickness,
                'shape_color': el.shape_color,
                # Image (base64 encoded)
                'image_data': el.image_data.decode('ascii') if el.image_data else False,
                'image_width': el.image_width,
            }
            elements.append(el_data)

        export_data = {
            '_export_format': 'vpa_label_designer',
            '_version': '1.0',
            'template': {
                'name': self.name,
                'model_name': self.model_name,
                'is_default': self.is_default,
                'rfid_data_variable_name': (
                    self.rfid_data_variable_id.name
                    if self.rfid_data_variable_id else False
                ),
            },
            'label_size': size_data,
            'elements': elements,
        }

        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
        json_b64 = base64.b64encode(json_str.encode('utf-8'))

        filename = f'{self.name or "label_template"}.vpa'
        # Sanitize filename
        filename = re.sub(r'[^\w\s\-.]', '', filename).strip()
        if not filename.endswith('.vpa'):
            filename += '.vpa'

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': json_b64,
            'mimetype': 'application/octet-stream',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
