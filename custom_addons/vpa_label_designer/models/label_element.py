# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

import base64
import io
import logging

from PIL import Image

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class LabelElement(models.Model):
    _name = 'vpa.label.element'
    _description = 'Label Element'
    _order = 'sequence, id'

    template_id = fields.Many2one('vpa.label.template', string='Template',
                                  required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Description')

    element_type = fields.Selection([
        ('text', 'Static Text'),
        ('variable', 'Variable Field'),
        ('barcode', 'Barcode'),
        ('qr_code', 'QR Code'),
        ('line', 'Line'),
        ('v_line', 'Vertical Line'),
        ('box', 'Box / Rectangle'),
        ('image', 'Image'),
        ('company_logo', 'Company Logo'),
    ], string='Type', required=True, default='text')

    # Position (in dots)
    pos_x = fields.Integer(string='X Position (dots)', default=0)
    pos_y = fields.Integer(string='Y Position (dots)', default=0)

    # Text settings
    content = fields.Char(string='Content / Text',
                          help='Static text or {{VARIABLE_NAME}} placeholder')
    font_id = fields.Selection([
        ('0', '0 - Default Proportional'),
        ('A', 'A - 9x5'),
        ('B', 'B - 11x7'),
        ('C', 'C - 18x10'),
        ('D', 'D - 18x10'),
        ('E', 'E - 28x15'),
        ('F', 'F - 26x13'),
        ('G', 'G - 60x40'),
        ('H', 'H - 21x13'),
    ], string='Font', default='0')
    font_height = fields.Integer(string='Font Height (dots)', default=30)
    font_width = fields.Integer(string='Font Width (dots)', default=0,
                                help='0 = auto-scale to match height')
    rotation = fields.Selection([
        ('N', 'Normal (0°)'),
        ('R', 'Rotated 90° CW'),
        ('I', 'Inverted 180°'),
        ('B', 'Bottom-up 270° CW'),
    ], string='Rotation', default='N')
    max_width = fields.Integer(
        string='Max Width (dots)', default=0,
        help='Maximum text width in dots. 0 = no limit.')
    max_lines = fields.Selection([
        ('1', '1 line (truncate)'),
        ('2', '2 lines'),
        ('3', '3 lines'),
        ('4', '4 lines'),
    ], string='Max Lines', default='1')
    text_alignment = fields.Selection([
        ('L', 'Left'),
        ('C', 'Center'),
        ('R', 'Right'),
    ], string='Alignment', default='L')

    # Variable settings
    variable_id = fields.Many2one('vpa.label.variable', string='Variable',
                                  help='Variable to resolve at print time')

    # Barcode settings
    barcode_type = fields.Selection([
        ('C', 'Code 128'),
        ('3', 'Code 39'),
        ('E', 'EAN-13'),
        ('U', 'UPC-A'),
        ('2', 'Interleaved 2 of 5'),
    ], string='Barcode Type', default='C')
    barcode_height = fields.Integer(string='Barcode Height (dots)', default=100)
    barcode_module_width = fields.Integer(string='Module Width', default=2,
                                         help='Width of the narrowest bar (1-10)')
    show_text_below = fields.Boolean(string='Show Text Below Barcode', default=True)

    # QR Code settings
    qr_magnification = fields.Integer(string='QR Magnification', default=5,
                                      help='QR module size (1-10)')
    qr_error_correction = fields.Selection([
        ('H', 'H - High (30%)'),
        ('Q', 'Q - Quartile (25%)'),
        ('M', 'M - Medium (15%)'),
        ('L', 'L - Low (7%)'),
    ], string='Error Correction', default='M')

    # Shape settings
    shape_width = fields.Integer(string='Width (dots)', default=100)
    shape_height = fields.Integer(string='Height (dots)', default=100)
    border_thickness = fields.Integer(string='Border Thickness (dots)', default=2)
    shape_color = fields.Selection([
        ('B', 'Black'),
        ('W', 'White'),
    ], string='Color', default='B')

    # Image settings
    image_data = fields.Binary(string='Image', attachment=True)
    image_width = fields.Integer(string='Image Width (dots)', default=100)

    # Computed ZPL
    zpl_snippet = fields.Text(string='ZPL Code', compute='_compute_zpl_snippet')

    @api.onchange('name')
    def _onchange_name(self):
        """Auto-populate content from name for text elements if content is empty."""
        if self.element_type in ('text', 'barcode', 'qr_code') and self.name and not self.content:
            self.content = self.name

    @api.onchange('element_type')
    def _onchange_element_type(self):
        """Set sensible defaults when element type changes."""
        if self.element_type == 'variable':
            self.content = False
        elif self.element_type in ('text',) and self.name and not self.content:
            self.content = self.name

    @api.constrains('element_type', 'content', 'variable_id')
    def _check_required_fields(self):
        for rec in self:
            if rec.element_type in ('text', 'barcode', 'qr_code') and not rec.content:
                raise ValidationError(
                    _("Content is required for %s elements.", rec.element_type)
                )
            if rec.element_type == 'variable' and not rec.variable_id:
                raise ValidationError(
                    _("A variable must be selected for variable elements.")
                )

    @api.depends('element_type', 'pos_x', 'pos_y', 'content', 'font_id',
                 'font_height', 'font_width', 'rotation', 'variable_id',
                 'barcode_type', 'barcode_height', 'barcode_module_width',
                 'show_text_below', 'qr_magnification', 'qr_error_correction',
                 'shape_width', 'shape_height', 'border_thickness', 'shape_color',
                 'image_data', 'image_width', 'max_width', 'max_lines',
                 'text_alignment')
    def _compute_zpl_snippet(self):
        for rec in self:
            if rec.element_type == 'text':
                rec.zpl_snippet = rec._zpl_text(rec.content or '')
            elif rec.element_type == 'variable':
                var_name = rec.variable_id.name if rec.variable_id else 'UNKNOWN'
                zpl = rec._zpl_text('{{%s}}' % var_name)
                # Add VAT note below price variables in smaller font
                if var_name == 'PRODUCT_PRICE':
                    zpl += rec._zpl_vat_note('Excl. VAT')
                elif var_name == 'PRODUCT_PRICE_INCL':
                    zpl += rec._zpl_vat_note('Incl. VAT')
                rec.zpl_snippet = zpl
            elif rec.element_type == 'barcode':
                rec.zpl_snippet = rec._zpl_barcode(rec.content or '{{PRODUCT_BARCODE}}')
            elif rec.element_type == 'qr_code':
                rec.zpl_snippet = rec._zpl_qr_code(rec.content or '{{PRODUCT_BARCODE}}')
            elif rec.element_type == 'line':
                rec.zpl_snippet = rec._zpl_line()
            elif rec.element_type == 'v_line':
                rec.zpl_snippet = rec._zpl_v_line()
            elif rec.element_type == 'box':
                rec.zpl_snippet = rec._zpl_box()
            elif rec.element_type == 'image':
                rec.zpl_snippet = rec._zpl_image()
            elif rec.element_type == 'company_logo':
                rec.zpl_snippet = rec._zpl_company_logo()
            else:
                rec.zpl_snippet = ''

    def _zpl_text(self, content):
        """Generate ZPL for text element."""
        font = self.font_id or '0'
        rot = self.rotation or 'N'
        height = self.font_height or 30
        width = self.font_width or 0
        lines = int(self.max_lines or '1')
        align = self.text_alignment or 'L'
        zpl = f'^FO{self.pos_x},{self.pos_y}^A{font}{rot},{height},{width}'
        if self.max_width and self.max_width > 0:
            # ^FB{width},{max_lines},{line_spacing},{justification}
            zpl += f'^FB{self.max_width},{lines},0,{align}'
        zpl += f'^FD{content}^FS'
        return zpl

    def _zpl_vat_note(self, note_text):
        """Generate a smaller ZPL text line below the current element for VAT indication.
        Inherits alignment from the price element (via max_width + text_alignment).
        """
        height = self.font_height or 30
        # VAT note is ~60% of the price font size, minimum 16 dots
        note_height = max(16, int(height * 0.6))
        # Position below the price text
        note_y = self.pos_y + height + 4
        font = self.font_id or '0'
        rot = self.rotation or 'N'
        align = self.text_alignment or 'L'
        zpl = f'\n^FO{self.pos_x},{note_y}^A{font}{rot},{note_height},0'
        # Use ^FB to match alignment when max_width is set
        if self.max_width and self.max_width > 0:
            zpl += f'^FB{self.max_width},1,0,{align}'
        zpl += f'^FD({note_text})^FS'
        return zpl

    def _zpl_barcode(self, content):
        """Generate ZPL for barcode element."""
        bc_type = self.barcode_type or 'C'
        rot = self.rotation or 'N'
        height = self.barcode_height or 100
        module_w = self.barcode_module_width or 2
        show_text = 'Y' if self.show_text_below else 'N'
        bc_cmd = f'B{bc_type}'
        return f'^FO{self.pos_x},{self.pos_y}^BY{module_w}^{bc_cmd}{rot},{height},{show_text},N^FD{content}^FS'

    def _zpl_qr_code(self, content):
        """Generate ZPL for QR code element."""
        mag = self.qr_magnification or 5
        ec = self.qr_error_correction or 'M'
        return f'^FO{self.pos_x},{self.pos_y}^BQN,2,{mag}^FD{ec}A,{content}^FS'

    def _zpl_line(self):
        """Generate ZPL for line element (uses graphic box with minimal height/width)."""
        w = self.shape_width or 100
        h = self.border_thickness or 2
        color = self.shape_color or 'B'
        return f'^FO{self.pos_x},{self.pos_y}^GB{w},{h},{h},{color}^FS'

    def _zpl_v_line(self):
        """Generate ZPL for vertical line element (uses graphic box with minimal width)."""
        w = self.border_thickness or 2
        h = self.shape_height or 100
        color = self.shape_color or 'B'
        return f'^FO{self.pos_x},{self.pos_y}^GB{w},{h},{w},{color}^FS'

    def _zpl_box(self):
        """Generate ZPL for box/rectangle element."""
        w = self.shape_width or 100
        h = self.shape_height or 100
        t = self.border_thickness or 2
        color = self.shape_color or 'B'
        return f'^FO{self.pos_x},{self.pos_y}^GB{w},{h},{t},{color}^FS'

    def _zpl_image(self):
        """Generate ZPL for image element using GRF conversion."""
        if not self.image_data:
            return ''
        return self._image_to_grf_zpl(self.image_data, self.image_width or 100)

    def _zpl_company_logo(self):
        """Generate ZPL for company logo element."""
        company = self.env.company
        if not company.logo:
            return ''
        return self._image_to_grf_zpl(company.logo, self.image_width or 100)

    def _image_to_grf_zpl(self, image_b64, target_width):
        """Convert a base64-encoded image to ZPL ^GFA command.

        Args:
            image_b64: Base64-encoded image data
            target_width: Target width in dots (pixels)

        Returns:
            str: ZPL ^GFA command string
        """
        try:
            raw = base64.b64decode(image_b64)
            img = Image.open(io.BytesIO(raw))

            # Convert to RGBA first to handle transparency
            img = img.convert('RGBA')
            # Create white background for transparent areas
            bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
            bg.paste(img, mask=img.split()[3])  # Alpha channel as mask
            img = bg.convert('L')  # Convert to grayscale

            # Resize preserving aspect ratio
            if target_width and target_width != img.width:
                ratio = target_width / img.width
                new_h = max(1, int(img.height * ratio))
                img = img.resize((target_width, new_h), Image.LANCZOS)

            # Sharpen and boost contrast for cleaner output
            from PIL import ImageEnhance, ImageFilter
            img = img.filter(ImageFilter.SHARPEN)
            img = ImageEnhance.Contrast(img).enhance(2.0)

            # Convert to monochrome — use hard threshold for crisp logos
            # (no dithering, which would introduce stipple patterns)
            img = img.point(lambda p: 0 if p < 100 else 255, '1')

            width_px = img.width
            height_px = img.height
            bytes_per_row = (width_px + 7) // 8
            total_bytes = bytes_per_row * height_px

            # Build hex data row by row
            hex_parts = []
            pixels = img.load()
            for y in range(height_px):
                for bx in range(bytes_per_row):
                    byte_val = 0
                    for bit in range(8):
                        px = bx * 8 + bit
                        if px < width_px:
                            # PIL '1' mode: 0=black, 255=white
                            # ZPL GRF: 1=black, 0=white (inverted)
                            if pixels[px, y] == 0:
                                byte_val |= (1 << (7 - bit))
                    hex_parts.append(f'{byte_val:02X}')

            grf_data = ''.join(hex_parts)
            return (
                f'^FO{self.pos_x},{self.pos_y}'
                f'^GFA,{total_bytes},{total_bytes},{bytes_per_row},{grf_data}'
                f'^FS'
            )
        except Exception:
            _logger.warning('Failed to convert image to GRF for element %s', self.id, exc_info=True)
            return ''

    def get_display_content(self):
        """Get human-readable content description for the element."""
        self.ensure_one()
        if self.element_type == 'text':
            return self.content or '(empty)'
        elif self.element_type == 'variable':
            return f'{{{{{self.variable_id.name}}}}}' if self.variable_id else '(no variable)'
        elif self.element_type == 'barcode':
            bc_names = dict(self._fields['barcode_type'].selection)
            return f'{bc_names.get(self.barcode_type, "Barcode")}: {self.content or "{{PRODUCT_BARCODE}}"}'
        elif self.element_type == 'qr_code':
            return f'QR: {self.content or "{{PRODUCT_BARCODE}}"}'
        elif self.element_type == 'line':
            return f'H-Line ({self.shape_width}x{self.border_thickness})'
        elif self.element_type == 'v_line':
            return f'V-Line ({self.border_thickness}x{self.shape_height})'
        elif self.element_type == 'box':
            return f'Box ({self.shape_width}x{self.shape_height})'
        elif self.element_type == 'image':
            return f'Image ({self.image_width}px wide)'
        elif self.element_type == 'company_logo':
            return f'Company Logo ({self.image_width}px wide)'
        return ''
