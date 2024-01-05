# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"
    default_code = fields.Char(compute="_compute_internal_ref")
    def get_or_create_ir_sequence(self):
        sequence_code = f"product_category_{self.categ_id.short_name}"
        IrSequence = self.env["ir.sequence"].search([("code","=", sequence_code)])
        if IrSequence.exists():
           return IrSequence.next_by_code(sequence_code)
        return self.env["ir.sequence"].create({
              "name": f"Product Internal Reference Sequence: {self.categ_id.short_name}",
              "code": sequence_code,
              "padding": 5,
              "number_next": 1,
              "number_increment": 1
           }).next_by_code(sequence_code)

    
    @api.depends("categ_id")
    def _compute_internal_ref(self):
        for record in self:
            if record.categ_id and record.categ_id.short_name and record.categ_id.parent_id.short_name:
               sequence = record.get_or_create_ir_sequence()
               record.default_code = f"{record.categ_id.parent_id.short_name}/{record.categ_id.short_name}/{sequence}"

    @api.model
    def create(self, vals):
        # Generate Internal Reference
        barcode = self.env["ir.sequence"].next_by_code("barcode.product.template")
        if not vals.get("barcode"):
           # Generate barcode number
           vals.update({"barcode":barcode})
        res = super(ProductTemplate, self).create(vals)
        return res

