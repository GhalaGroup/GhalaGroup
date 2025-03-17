# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

class ProductTemplate(models.Model):
   _inherit = "product.template"

   default_code = fields.Char(copy=False)

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

   
   def _generate_default_code(self):
      for record in self:
         if record.categ_id and record.categ_id.short_name and record.categ_id.parent_id.short_name:
            sequence = record.get_or_create_ir_sequence()
            parent_categories = self.env['product.category'].search([
               ('id', 'parent_of', record.categ_id.id)
            ], order="id asc")
            short_names = "/".join(parent_categories.mapped("short_name"))
            return f"{short_names}/{sequence}"
         return False

   
   def write(self, vals):
      result = super(ProductTemplate, self).write(vals)
      if "categ_id" in vals:
         for record in self:
            default_code = False
            if record.categ_id and record.categ_id.short_name and record.categ_id.parent_id.short_name:
               sequence_code = f"product_category_{record.categ_id.short_name}"
               IrSequence = self.env["ir.sequence"].search([("code","=", sequence_code)])
               if IrSequence.exists():
                  sequence =  IrSequence.next_by_code(sequence_code)
               else:
                  sequence = self.env["ir.sequence"].create({
                     "name": f"Product Internal Reference Sequence: {record.categ_id.short_name}",
                     "code": sequence_code,
                     "padding": 5,
                     "number_next": 1,
                     "number_increment": 1
                  }).next_by_code(sequence_code)
               parent_categories = self.env['product.category'].search([
                  ('id', 'parent_of', record.categ_id.id)
               ], order="id asc")
               short_names = "/".join(parent_categories.mapped("short_name"))
               default_code =  f"{short_names}/{sequence}"
            if default_code:
               super(ProductTemplate, record).write({'default_code': default_code})  # Avoid recursion by calling super
      return result
        
   @api.model
   def create(self, vals):
      res = super(ProductTemplate, self).create(vals)
      if "categ_id" in vals:
         default_code = res._generate_default_code()
         if default_code:
               res.write({'default_code': default_code})
      return res
   

   @api.returns('self', lambda value: value.id)
   def copy(self, default=None):
      default = default or {}
      template = super(ProductTemplate, self).copy(default)
      if template.default_code and template.categ_id.short_name:
         sequence_code = f"product_category_{template.categ_id.short_name}"
         IrSequence = self.env["ir.sequence"].search([("code","=", sequence_code)])
         if IrSequence.exists():
            IrSequence.number_next_actual -= 1
         template.default_code = ""
      return template

