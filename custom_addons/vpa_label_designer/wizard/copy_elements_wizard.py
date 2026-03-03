# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CopyElementsWizardLine(models.TransientModel):
    _name = 'vpa.copy.elements.wizard.line'
    _description = 'Copy Elements Wizard Line'
    _order = 'sequence'

    wizard_id = fields.Many2one('vpa.copy.elements.wizard', required=True, ondelete='cascade')
    element_id = fields.Many2one('vpa.label.element', string='Element', required=True)
    sequence = fields.Integer(related='element_id.sequence', store=True)
    element_type = fields.Selection(related='element_id.element_type', string='Type')
    name = fields.Char(related='element_id.name', string='Name')
    content_preview = fields.Char(string='Content', compute='_compute_content_preview')
    selected = fields.Boolean(string='Copy', default=True)

    @api.depends('element_id', 'element_id.element_type', 'element_id.content',
                 'element_id.variable_id', 'element_id.font_height')
    def _compute_content_preview(self):
        for rec in self:
            el = rec.element_id
            if not el:
                rec.content_preview = ''
                continue
            if el.element_type == 'variable' and el.variable_id:
                rec.content_preview = f'{{{{{el.variable_id.name}}}}}'
            elif el.element_type in ('text',):
                rec.content_preview = (el.content or '')[:40]
            elif el.element_type == 'barcode':
                rec.content_preview = el.content or '(barcode)'
            elif el.element_type == 'qr_code':
                rec.content_preview = el.content or '(qr code)'
            elif el.element_type == 'company_logo':
                rec.content_preview = '(company logo)'
            elif el.element_type == 'image':
                rec.content_preview = '(image)'
            elif el.element_type in ('line', 'v_line'):
                rec.content_preview = f'{el.shape_width}px'
            elif el.element_type == 'box':
                rec.content_preview = f'{el.shape_width}x{el.shape_height}px'
            else:
                rec.content_preview = ''


class CopyElementsWizard(models.TransientModel):
    _name = 'vpa.copy.elements.wizard'
    _description = 'Copy Elements from Another Label Template'

    target_template_id = fields.Many2one(
        'vpa.label.template', string='Target Template',
        required=True, readonly=True)

    source_template_id = fields.Many2one(
        'vpa.label.template', string='Copy From Template',
        required=False,
        domain="[('id', '!=', target_template_id)]",
        help='Select the label template to copy elements from')

    element_line_ids = fields.One2many(
        'vpa.copy.elements.wizard.line', 'wizard_id',
        string='Elements to Copy')

    replace_existing = fields.Boolean(
        string='Replace Existing Elements',
        default=False,
        help='If checked, all existing elements in the current template will be removed before copying')

    selected_count = fields.Integer(
        string='Selected', compute='_compute_selected_count')

    @api.depends('element_line_ids.selected')
    def _compute_selected_count(self):
        for rec in self:
            rec.selected_count = sum(1 for l in rec.element_line_ids if l.selected)

    @api.onchange('source_template_id')
    def _onchange_source_template(self):
        """Populate element lines when source template is chosen."""
        self.element_line_ids = [(5, 0, 0)]  # clear
        if not self.source_template_id:
            return
        lines = []
        for el in self.source_template_id.element_ids.sorted('sequence'):
            lines.append((0, 0, {
                'element_id': el.id,
                'selected': True,
            }))
        self.element_line_ids = lines

    def action_select_all(self):
        self.element_line_ids.write({'selected': True})

    def action_deselect_all(self):
        self.element_line_ids.write({'selected': False})

    def _scale_position(self, value, src_dim, tgt_dim):
        """Scale a position/size value from source to target label dimensions."""
        if not src_dim or src_dim == tgt_dim:
            return value
        return int(round(value * tgt_dim / src_dim))

    def _fit_element(self, el, src_w, src_h, tgt_w, tgt_h):
        """Return scaled and clamped pos_x, pos_y, max_width for an element."""
        pos_x = self._scale_position(el.pos_x, src_w, tgt_w)
        pos_y = self._scale_position(el.pos_y, src_h, tgt_h)
        # Clamp to target bounds
        pos_x = max(0, min(pos_x, tgt_w - 1))
        pos_y = max(0, min(pos_y, tgt_h - 1))
        # Scale max_width if set
        max_width = el.max_width or 0
        if max_width:
            max_width = self._scale_position(max_width, src_w, tgt_w)
            # Clamp so it doesn't exceed label right edge
            max_width = min(max_width, tgt_w - pos_x)
        return pos_x, pos_y, max_width

    def action_copy(self):
        self.ensure_one()
        if not self.source_template_id:
            raise UserError(_("Please select a source template."))

        selected_lines = self.element_line_ids.filtered('selected')
        if not selected_lines:
            raise UserError(_("Please select at least one element to copy."))

        target = self.target_template_id
        source = self.source_template_id

        # Get source and target label dimensions for scaling
        src_w = source.label_size_id.width_dots or 639
        src_h = source.label_size_id.height_dots or 639
        tgt_w = target.label_size_id.width_dots or 639
        tgt_h = target.label_size_id.height_dots or 639

        removed_count = 0
        if self.replace_existing and target.element_ids:
            removed_count = len(target.element_ids)
            target.element_ids.unlink()

        copied_count = 0
        for line in selected_lines.sorted('sequence'):
            el = line.element_id
            pos_x, pos_y, max_width = self._fit_element(el, src_w, src_h, tgt_w, tgt_h)
            self.env['vpa.label.element'].create({
                'template_id': target.id,
                'sequence': el.sequence,
                'name': el.name,
                'element_type': el.element_type,
                'pos_x': pos_x,
                'pos_y': pos_y,
                'content': el.content,
                'font_id': el.font_id,
                'font_height': el.font_height,
                'font_width': el.font_width,
                'rotation': el.rotation,
                'max_width': max_width,
                'max_lines': el.max_lines,
                'text_alignment': el.text_alignment,
                'variable_id': el.variable_id.id if el.variable_id else False,
                'barcode_type': el.barcode_type,
                'barcode_height': el.barcode_height,
                'barcode_module_width': el.barcode_module_width,
                'show_text_below': el.show_text_below,
                'qr_magnification': el.qr_magnification,
                'qr_error_correction': el.qr_error_correction,
                'shape_width': el.shape_width,
                'shape_height': el.shape_height,
                'border_thickness': el.border_thickness,
                'shape_color': el.shape_color,
                'image_data': el.image_data if el.element_type == 'image' else False,
                'image_width': el.image_width,
            })
            copied_count += 1

        msg_parts = [f"<b>Copied {copied_count} elements</b> from <b>{self.source_template_id.name}</b>"]
        if removed_count:
            msg_parts.append(f"({removed_count} existing elements replaced)")
        target.message_post(body=' '.join(msg_parts))

        return {'type': 'ir.actions.act_window_close'}

    def action_open_wizard(self):
        """Called from template form button."""
        template_id = self.env.context.get('active_id')
        if not template_id:
            raise UserError(_("No template selected."))
        wizard = self.create({'target_template_id': template_id})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Copy Elements from Template'),
            'res_model': 'vpa.copy.elements.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }
