# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

import json

from odoo import api, fields, models
from odoo.exceptions import UserError


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
    printer_id = fields.Many2one('vpa.printer.config', string='Printer',
                                 required=True)
    copies = fields.Integer(string='Copies per Record', default=1,
                            help='Number of label copies per record (for standard flow)')

    # Source info
    source_model = fields.Char(string='Source Model')
    source_ids = fields.Char(string='Source Record IDs',
                             help='JSON list of record IDs')

    # PO / Receipt flow - per-line detail
    line_ids = fields.One2many('vpa.print.label.wizard.line', 'wizard_id',
                               string='Label Lines')
    is_quantity_mode = fields.Boolean(string='Quantity Mode',
                                     help='True when printing from PO/Receipt with per-line quantities')

    # Preview
    preview_zpl = fields.Text(string='Preview ZPL', readonly=True)
    total_labels = fields.Integer(string='Total Labels', compute='_compute_total_labels')

    @api.depends('copies', 'line_ids', 'line_ids.label_qty', 'is_quantity_mode', 'source_ids')
    def _compute_total_labels(self):
        for rec in self:
            if rec.is_quantity_mode:
                rec.total_labels = sum(rec.line_ids.mapped('label_qty'))
            else:
                try:
                    ids_list = json.loads(rec.source_ids or '[]')
                    rec.total_labels = len(ids_list) * (rec.copies or 1)
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

            # Set default printer
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
            default_template = self.env['vpa.label.template'].search([
                ('model_name', '=', template_model),
                ('company_id', 'in', [False, self.env.company.id]),
            ], limit=1)
            if default_template:
                res['template_id'] = default_template.id

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
                record = self.env[self.source_model].browse(source_ids[0])
                preview = self.template_id.resolve_zpl_for_record(record)
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
