# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

import base64
import json
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ImportLabelWizard(models.TransientModel):
    _name = 'vpa.import.label.wizard'
    _description = 'Restore Label Template'

    file_data = fields.Binary(string='Template File', required=True,
                              help='Select a .vpa file backed up from VPA Label Designer')
    file_name = fields.Char(string='File Name')

    def action_import(self):
        """Restore a label template from a .vpa backup file."""
        self.ensure_one()
        if not self.file_data:
            raise UserError(_("Please select a file to restore."))

        try:
            raw = base64.b64decode(self.file_data)
            data = json.loads(raw.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise UserError(_("Invalid file format. Please upload a valid .vpa file backed up from VPA Label Designer.\n\nError: %s") % str(e))

        # Validate format
        if data.get('_export_format') != 'vpa_label_designer':
            raise UserError(_("This file is not a valid VPA Label Designer backup."))

        template_data = data.get('template', {})
        size_data = data.get('label_size', {})
        elements_data = data.get('elements', [])

        if not template_data or not size_data:
            raise UserError(_("The file is missing template or label size data."))

        # Find or create label size
        label_size = self._find_or_create_size(size_data)

        # Resolve RFID variable
        rfid_var_id = False
        rfid_var_name = template_data.get('rfid_data_variable_name')
        if rfid_var_name:
            rfid_var = self.env['vpa.label.variable'].search(
                [('name', '=', rfid_var_name)], limit=1)
            if rfid_var:
                rfid_var_id = rfid_var.id

        # Create template
        template = self.env['vpa.label.template'].create({
            'name': template_data.get('name', 'Imported Template'),
            'model_name': template_data.get('model_name', 'product.product'),
            'label_size_id': label_size.id,
            'is_default': False,  # Never auto-set as default on import
            'rfid_data_variable_id': rfid_var_id,
        })

        # Create elements
        for el_data in elements_data:
            self._create_element(template, el_data)

        # Open the imported template
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.label.template',
            'res_id': template.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _find_or_create_size(self, size_data):
        """Find an existing label size with matching dimensions or create a new one."""
        LabelSize = self.env['vpa.label.size']

        # Try exact match on dimensions and DPI
        existing = LabelSize.search([
            ('width_mm', '=', size_data.get('width_mm')),
            ('height_mm', '=', size_data.get('height_mm')),
            ('dpi', '=', size_data.get('dpi', '203')),
        ], limit=1)

        if existing:
            return existing

        # Create new size
        return LabelSize.create({
            'name': size_data.get('name', 'Imported Label Size'),
            'width_mm': size_data.get('width_mm'),
            'height_mm': size_data.get('height_mm'),
            'dpi': size_data.get('dpi', '203'),
            'has_rfid': size_data.get('has_rfid', False),
            'rfid_position': size_data.get('rfid_position', 'center'),
        })

    def _create_element(self, template, el_data):
        """Create a single label element from export data."""
        # Resolve variable reference
        variable_id = False
        var_name = el_data.get('variable_name')
        if var_name:
            var_rec = self.env['vpa.label.variable'].search(
                [('name', '=', var_name)], limit=1)
            if var_rec:
                variable_id = var_rec.id
            else:
                _logger.warning(
                    "Variable '%s' not found during import. "
                    "Element will be created without variable reference.", var_name)

        vals = {
            'template_id': template.id,
            'sequence': el_data.get('sequence', 10),
            'name': el_data.get('name'),
            'element_type': el_data.get('element_type', 'text'),
            'pos_x': el_data.get('pos_x', 0),
            'pos_y': el_data.get('pos_y', 0),
            'content': el_data.get('content'),
            'font_id': el_data.get('font_id', '0'),
            'font_height': el_data.get('font_height', 30),
            'font_width': el_data.get('font_width', 0),
            'rotation': el_data.get('rotation', 'N'),
            'max_width': el_data.get('max_width', 0),
            'max_lines': el_data.get('max_lines', '1'),
            'text_alignment': el_data.get('text_alignment', 'L'),
            'variable_id': variable_id,
            'barcode_type': el_data.get('barcode_type', 'C'),
            'barcode_height': el_data.get('barcode_height', 100),
            'barcode_module_width': el_data.get('barcode_module_width', 2),
            'show_text_below': el_data.get('show_text_below', True),
            'qr_magnification': el_data.get('qr_magnification', 5),
            'qr_error_correction': el_data.get('qr_error_correction', 'M'),
            'shape_width': el_data.get('shape_width', 100),
            'shape_height': el_data.get('shape_height', 100),
            'border_thickness': el_data.get('border_thickness', 2),
            'shape_color': el_data.get('shape_color', 'B'),
            'image_data': el_data.get('image_data') or False,
            'image_width': el_data.get('image_width', 100),
        }
        self.env['vpa.label.element'].create(vals)
