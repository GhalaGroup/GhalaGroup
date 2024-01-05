# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = "product.product"
    def _compute_internal_ref(self):
        for record in self:
            if not record.default_code and record.product_tmpl_id.categ_id and record.product_tmpl_id.categ_id.short_name and record.product_tmpl_id.categ_id.parent_id.short_name:
               sequence = record.product_tmpl_id.get_or_create_ir_sequence()
               record.default_code = f"{record.product_tmpl_id.categ_id.parent_id.short_name}/{record.product_tmpl_id.categ_id.short_name}/{sequence}"

    @api.model
    def create(self, vals):
        # Generate Barcode
        barcode = self.env["ir.sequence"].next_by_code("barcode.product.template")
        if not vals.get("barcode"):
           # Generate barcode number
           vals.update({"barcode":barcode})
        res = super(ProductProduct, self).create(vals)
        # Compute Internal reference
        res._compute_internal_ref()
        return res

