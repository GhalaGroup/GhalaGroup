# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

import base64
import json
import logging

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PrintLabelWizard(models.TransientModel):
    _name = 'vpa.print.label.wizard'
    _description = 'Print Label Wizard'

    state = fields.Selection([
        ('select', 'Select'),
        ('preview', 'Preview'),
        ('done', 'Done'),
    ], string='State', default='select')

    template_id = fields.Many2one('vpa.label.template', string='Label Template',
                                  required=True)
    printer_id = fields.Many2one('vpa.printer.config', string='Printer')
    copies = fields.Integer(string='Copies per Record', default=1,
                            help='Number of label copies per record (for standard flow)')

    # Source info
    source_model = fields.Char(string='Source Model')
    source_ids = fields.Char(string='Source Record IDs',
                             help='JSON list of record IDs')

    # Variant selection (only used when source_model == product.template with multiple variants)
    variant_ids = fields.Many2many(
        'product.product', string='Variants',
        help='Select which variants to print. Leave empty to print all variants.')
    available_variant_ids = fields.Many2many(
        'product.product', 'vpa_print_wizard_avail_variant_rel',
        string='Available Variants', compute='_compute_available_variants')
    has_multiple_variants = fields.Boolean(compute='_compute_available_variants')

    # PO / Receipt flow - per-line detail
    line_ids = fields.One2many('vpa.print.label.wizard.line', 'wizard_id',
                               string='Label Lines')
    is_quantity_mode = fields.Boolean(string='Quantity Mode',
                                     help='True when printing from PO/Receipt with per-line quantities')

    # Preview
    preview_zpl = fields.Text(string='Preview ZPL', readonly=True)
    total_labels = fields.Integer(string='Total Labels', compute='_compute_total_labels')

    @api.depends('source_model', 'source_ids')
    def _compute_available_variants(self):
        for rec in self:
            if rec.source_model == 'product.template':
                try:
                    ids_list = json.loads(rec.source_ids or '[]')
                    templates = self.env['product.template'].browse(ids_list)
                    variants = templates.mapped('product_variant_ids')
                    rec.available_variant_ids = variants
                    rec.has_multiple_variants = len(variants) > 1
                except (json.JSONDecodeError, TypeError):
                    rec.available_variant_ids = False
                    rec.has_multiple_variants = False
            else:
                rec.available_variant_ids = False
                rec.has_multiple_variants = False

    @api.depends('copies', 'line_ids', 'line_ids.label_qty', 'is_quantity_mode', 'source_ids',
                 'variant_ids', 'has_multiple_variants')
    def _compute_total_labels(self):
        for rec in self:
            if rec.is_quantity_mode:
                rec.total_labels = sum(rec.line_ids.mapped('label_qty'))
            else:
                try:
                    ids_list = json.loads(rec.source_ids or '[]')
                    if rec.source_model == 'product.template':
                        if rec.variant_ids:
                            count = len(rec.variant_ids)
                        else:
                            templates = self.env['product.template'].browse(ids_list)
                            count = len(templates.mapped('product_variant_ids'))
                    else:
                        count = len(ids_list)
                    rec.total_labels = count * (rec.copies or 1)
                except (json.JSONDecodeError, TypeError):
                    rec.total_labels = 0

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids', [])

        if active_model:
            res['source_model'] = active_model
            res['source_ids'] = json.dumps(active_ids)

            # Set default printer: user preference first, then company default
            user_printer = self.env.user.default_printer_id
            if user_printer:
                res['printer_id'] = user_printer.id
            else:
                default_printer = self.env['vpa.printer.config'].search([
                    ('is_default', '=', True),
                    ('company_id', 'in', [False, self.env.company.id]),
                ], limit=1)
                if default_printer:
                    res['printer_id'] = default_printer.id

            # Find matching templates
            model_map = {
                'product.product': 'product.product',
                'product.template': 'product.product',
                'stock.picking': 'stock.picking',
                'stock.lot': 'stock.lot',
                'mrp.production': 'mrp.production',
                'purchase.order': 'purchase.order',
            }
            template_model = model_map.get(active_model, active_model)

            # Find default template: prefer is_default, then first match
            default_template = self.env['vpa.label.template'].search([
                ('model_name', '=', template_model),
                ('company_id', 'in', [False, self.env.company.id]),
                ('is_default', '=', True),
            ], limit=1)
            if not default_template:
                default_template = self.env['vpa.label.template'].search([
                    ('model_name', '=', template_model),
                    ('company_id', 'in', [False, self.env.company.id]),
                ], limit=1)

            if default_template:
                res['template_id'] = default_template.id

            # For product.template with single variant, auto-select it
            if active_model == 'product.template':
                templates = self.env['product.template'].browse(active_ids)
                variants = templates.mapped('product_variant_ids')
                if len(variants) == 1:
                    res['variant_ids'] = [(6, 0, variants.ids)]

            # Quantity mode for PO and Picking
            if active_model == 'purchase.order':
                res['is_quantity_mode'] = True
                res['line_ids'] = self._prepare_po_lines(active_ids)
            elif active_model == 'stock.picking':
                res['is_quantity_mode'] = True
                res['line_ids'] = self._prepare_picking_lines(active_ids)

        return res

    def _prepare_po_lines(self, po_ids):
        """Prepare wizard lines from purchase order lines."""
        lines = []
        orders = self.env['purchase.order'].browse(po_ids)
        for order in orders:
            for po_line in order.order_line:
                if not po_line.product_id:
                    continue
                # Get alternative UoMs
                alt_uom_ids = po_line.product_id.product_tmpl_id.uom_conversion_ids.mapped('uom_id').ids
                lines.append((0, 0, {
                    'product_id': po_line.product_id.id,
                    'ordered_qty': po_line.product_qty,
                    'product_uom_id': po_line.product_uom_id.id,
                    'label_qty': int(po_line.product_qty),
                    'source_document': order.name,
                }))
        return lines

    def _prepare_picking_lines(self, picking_ids):
        """Prepare wizard lines from stock picking move lines."""
        lines = []
        pickings = self.env['stock.picking'].browse(picking_ids)
        for picking in pickings:
            for move in picking.move_ids:
                if not move.product_id:
                    continue
                qty = move.quantity if move.quantity else move.product_uom_qty
                lines.append((0, 0, {
                    'product_id': move.product_id.id,
                    'ordered_qty': qty,
                    'product_uom_id': move.product_uom_id.id,
                    'label_qty': int(qty),
                    'source_document': picking.name,
                }))
        return lines

    def action_preview(self):
        """Generate preview ZPL with sample/actual data."""
        self.ensure_one()
        if not self.template_id:
            raise UserError('Please select a label template.')

        if self.is_quantity_mode:
            # Preview first line only
            if self.line_ids:
                first_line = self.line_ids[0]
                extra_values = first_line._get_extra_values()
                preview = self.template_id.resolve_zpl_for_record(
                    first_line.product_id, extra_values)
            else:
                preview = self.template_id.zpl_preview
        else:
            # Standard flow - use sample values
            source_ids = json.loads(self.source_ids or '[]')
            if source_ids and self.source_model:
                if self.source_model == 'product.template':
                    if self.variant_ids:
                        record = self.variant_ids[0]
                    else:
                        tmpl = self.env['product.template'].browse(source_ids[0])
                        record = tmpl.product_variant_ids[:1]
                else:
                    record = self.env[self.source_model].browse(source_ids[0])
                preview = self.template_id.resolve_zpl_for_record(record) if record else self.template_id.zpl_preview
            else:
                preview = self.template_id.zpl_preview

        self.write({
            'state': 'preview',
            'preview_zpl': preview,
        })
        return self._reopen()

    def action_print(self):
        """Send ZPL to printer."""
        self.ensure_one()
        if not self.template_id:
            raise UserError('Please select a label template.')
        if not self.printer_id:
            raise UserError('Please select a printer.')

        zpl_list = []

        if self.is_quantity_mode:
            # Quantity mode: generate label_qty copies per line
            for line in self.line_ids:
                if line.label_qty <= 0:
                    continue
                extra_values = line._get_extra_values()
                zpl = self.template_id.resolve_zpl_for_record(
                    line.product_id, extra_values)
                for _i in range(line.label_qty):
                    zpl_list.append(zpl)
        else:
            # Standard mode: copies per record
            source_ids = json.loads(self.source_ids or '[]')
            if source_ids and self.source_model:
                if self.source_model == 'product.template':
                    if self.variant_ids:
                        records = self.variant_ids
                    else:
                        templates = self.env['product.template'].browse(source_ids)
                        records = templates.mapped('product_variant_ids')
                else:
                    records = self.env[self.source_model].browse(source_ids)
                for record in records:
                    zpl = self.template_id.resolve_zpl_for_record(record)
                    for _i in range(self.copies or 1):
                        zpl_list.append(zpl)

        if not zpl_list:
            raise UserError('No labels to print. Please check your selection.')

        result = self.printer_id.send_zpl(zpl_list)

        self.write({'state': 'done'})

        return result

    def action_download_pdf(self):
        """Generate PDF of all labels via Labelary API and trigger download."""
        self.ensure_one()
        if not self.template_id:
            raise UserError('Please select a label template.')

        # Build the list of ZPL labels (same logic as action_print)
        zpl_list = []
        if self.is_quantity_mode:
            for line in self.line_ids:
                if line.label_qty <= 0:
                    continue
                extra_values = line._get_extra_values()
                zpl = self.template_id.resolve_zpl_for_record(
                    line.product_id, extra_values)
                for _i in range(line.label_qty):
                    zpl_list.append(zpl)
        else:
            source_ids = json.loads(self.source_ids or '[]')
            if source_ids and self.source_model:
                if self.source_model == 'product.template':
                    if self.variant_ids:
                        records = self.variant_ids
                    else:
                        templates = self.env['product.template'].browse(source_ids)
                        records = templates.mapped('product_variant_ids')
                else:
                    records = self.env[self.source_model].browse(source_ids)
                for record in records:
                    zpl = self.template_id.resolve_zpl_for_record(record)
                    for _i in range(self.copies or 1):
                        zpl_list.append(zpl)

        if not zpl_list:
            raise UserError('No labels to export. Please check your selection.')

        # Combine all labels into one ZPL string
        combined_zpl = '\n'.join(zpl_list)

        # Call Labelary API for PDF
        tmpl = self.template_id
        try:
            url = (
                f'http://api.labelary.com/v1/printers/{tmpl.label_dpmm}dpmm'
                f'/labels/{tmpl.label_width_inch}x{tmpl.label_height_inch}/0/'
            )
            response = requests.post(
                url,
                data=combined_zpl.encode('utf-8'),
                headers={'Accept': 'application/pdf'},
                timeout=30,
            )

            if response.status_code != 200:
                raise UserError(
                    f'Labelary API returned status {response.status_code}. '
                    'Please try again or check your label design.'
                )
        except requests.Timeout:
            raise UserError('Labelary API request timed out. Please try again.')
        except requests.ConnectionError:
            raise UserError(
                'Could not connect to Labelary API. '
                'Please check your internet connection.'
            )

        pdf_b64 = base64.b64encode(response.content)
        filename = f'{tmpl.name or "labels"}.pdf'
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

    def action_back(self):
        """Go back to select state."""
        self.ensure_one()
        self.write({'state': 'select', 'preview_zpl': False})
        return self._reopen()

    def _reopen(self):
        """Re-open the wizard to refresh the view."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
