# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PrintLabelWizardLine(models.TransientModel):
    _name = 'vpa.print.label.wizard.line'
    _description = 'Print Label Wizard Line'
    _order = 'id'

    wizard_id = fields.Many2one('vpa.print.label.wizard', string='Wizard',
                                required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product')
    product_sku = fields.Char(related='product_id.default_code', string='SKU')
    product_barcode = fields.Char(related='product_id.barcode', string='Barcode')

    # Quantities
    ordered_qty = fields.Float(string='Ordered Qty', readonly=True, digits=(16, 2))
    product_uom_id = fields.Many2one('uom.uom', string='PO UoM', readonly=True)
    label_qty = fields.Integer(string='Labels to Print', default=1,
                               help='Number of labels to print for this product (editable)')

    # Alternative UoM (from vpa_uom)
    alt_uom_id = fields.Many2one('uom.uom', string='Label UoM',
                                 help='Alternative UoM for label content. '
                                      'Leave empty to use the PO UoM.')
    available_alt_uom_ids = fields.Many2many('uom.uom', string='Available Alt UoMs',
                                             compute='_compute_available_alt_uoms')
    alt_uom_barcode = fields.Char(string='Label Barcode', compute='_compute_alt_uom_info')
    alt_uom_qty_per_package = fields.Float(string='Qty/Pkg', compute='_compute_alt_uom_info')
    alt_uom_packaging_name = fields.Char(string='Packaging', compute='_compute_alt_uom_info')

    source_document = fields.Char(string='Source')

    @api.depends('product_id')
    def _compute_available_alt_uoms(self):
        for line in self:
            if line.product_id:
                conversions = line.product_id.product_tmpl_id.uom_conversion_ids
                uom_ids = conversions.mapped('uom_id').ids
                # Include the base UoM
                base_uom = line.product_id.uom_id
                if base_uom and base_uom.id not in uom_ids:
                    uom_ids.append(base_uom.id)
                line.available_alt_uom_ids = [(6, 0, uom_ids)]
            else:
                line.available_alt_uom_ids = [(5,)]

    @api.depends('product_id', 'alt_uom_id')
    def _compute_alt_uom_info(self):
        for line in self:
            if line.alt_uom_id and line.product_id:
                conversion = line.product_id.product_tmpl_id.get_uom_conversion(line.alt_uom_id)
                if conversion:
                    line.alt_uom_barcode = conversion.barcode or line.product_id.barcode or ''
                    line.alt_uom_qty_per_package = conversion.qty_per_package
                    line.alt_uom_packaging_name = conversion.packaging_name or ''
                else:
                    # Base UoM selected
                    line.alt_uom_barcode = line.product_id.barcode or ''
                    line.alt_uom_qty_per_package = 0
                    line.alt_uom_packaging_name = ''
            else:
                line.alt_uom_barcode = line.product_id.barcode if line.product_id else ''
                line.alt_uom_qty_per_package = 0
                line.alt_uom_packaging_name = ''

    def _get_extra_values(self):
        """Get extra variable values for template resolution based on alt UoM selection."""
        self.ensure_one()
        values = {}

        if self.alt_uom_id and self.product_id:
            conversion = self.product_id.product_tmpl_id.get_uom_conversion(self.alt_uom_id)
            if conversion:
                values['ALT_UOM_NAME'] = conversion.uom_id.name or ''
                values['ALT_UOM_BARCODE'] = conversion.barcode or self.product_id.barcode or ''
                values['QTY_PER_PACKAGE'] = str(conversion.qty_per_package or '')
                values['PACKAGING_NAME'] = conversion.packaging_name or ''
            else:
                # Base UoM
                values['ALT_UOM_NAME'] = self.product_id.uom_id.name or ''
                values['ALT_UOM_BARCODE'] = self.product_id.barcode or ''
                values['QTY_PER_PACKAGE'] = ''
                values['PACKAGING_NAME'] = ''
        elif self.product_id:
            values['ALT_UOM_NAME'] = self.product_uom_id.name if self.product_uom_id else ''
            values['ALT_UOM_BARCODE'] = self.product_id.barcode or ''
            values['QTY_PER_PACKAGE'] = ''
            values['PACKAGING_NAME'] = ''

        if self.source_document:
            values['PO_NUMBER'] = self.source_document

        return values
