import math
import re


from odoo import models, fields, api, exceptions


class Madfox_Product(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        barcode = self.env['ir.sequence'].next_by_code('mf_barcode_seq')
        vals['barcode'] = barcode
        res = super(Madfox_Product, self).create(vals)
        # res.barcode = barcode
        if not res.default_code:
            res.default_code= self.getInternalNumber(res.categ_id.id)
        return res

    def getInternalNumber(self, categ_id):
        mad_seq = ""
        if self.type =='service':
		return mad_seq
        category = self.env['product.category'].search([('id', '=', categ_id)])
        if category:
            if not category.parent_id:
                raise exceptions.ValidationError('Please check if category has parent!')
            if not category.x_studio_category_short_code_field.x_name:
                raise exceptions.ValidationError('Please check if category has a short code!')
            if not self.env['ir.sequence'].search(
                    [('code', '=', 'mf_seq_' + str(category.parent_id.id) + '_' + str(category.id))]):
                raise exceptions.ValidationError('sequence not found!')
            seq1 = self.env['ir.sequence'].next_by_code('mf_seq_' + str(category.parent_id.id) + '_' + str(category.id))
            counter = category.complete_name.count('/')
            # raise UserError(seq1)
            if counter == 4:
                mad_seq = category.parent_id.parent_id.parent_id.parent_id.x_studio_category_short_code_field.x_name + "/" + category.parent_id.parent_id.parent_id.x_studio_category_short_code_field.x_name + "/" + category.parent_id.parent_id.x_studio_category_short_code_field.x_name + "/" + category.parent_id.x_studio_category_short_code_field.x_name + "/" + category.x_studio_category_short_code_field.x_name
            elif counter == 3:
                mad_seq = category.parent_id.parent_id.parent_id.x_studio_category_short_code_field.x_name + "/" + category.parent_id.parent_id.x_studio_category_short_code_field.x_name + "/" + category.parent_id.x_studio_category_short_code_field.x_name + "/" + category.x_studio_category_short_code_field.x_name
            elif counter == 2:
                mad_seq = category.parent_id.parent_id.x_studio_category_short_code_field.x_name + "/" + category.parent_id.x_studio_category_short_code_field.x_name + "/" + category.x_studio_category_short_code_field.x_name
            elif counter == 1:
                mad_seq = category.parent_id.x_studio_category_short_code_field.x_name + "/" + category.x_studio_category_short_code_field.x_name

            mad_seq = mad_seq + "/" + seq1
          
        return mad_seq
    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        if self.categ_id:
            self.default_code = self.getInternalNumber(self.categ_id.id)
            




class Madfox_ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals_list):
        templates = super(Madfox_ProductTemplate, self).create(vals_list)
        barcode = self.env['ir.sequence'].next_by_code('mf_barcode_seq')
        templates.barcode = barcode
       # templates.default_code=getSeq(self)
        return templates

    def getInternalNumber(self, categ_id):
        mad_seq = ""
        if self.type =='service':
		return mad_seq
        category = self.env['product.category'].search([('id', '=', categ_id)])
        if category:
            if not category.parent_id:
               # raise exceptions.ValidationError('Please check if category has parent!')
                return ''
            if not category.x_studio_category_short_code_field.x_name:
               # raise exceptions.ValidationError('Please check if category has a short code!')
                return ''
            if not self.env['ir.sequence'].search(
                    [('code', '=', 'mf_seq_' + str(category.parent_id.id) + '_' + str(category.id))]):
                raise exceptions.ValidationError('sequence not found!')
            seq1 = self.env['ir.sequence'].next_by_code(
                'mf_seq_' + str(category.parent_id.id) + '_' + str(category.id))
            counter = category.complete_name.count('/')
            # raise UserError(seq1)
            if counter == 4:
                mad_seq = category.parent_id.parent_id.parent_id.parent_id.x_studio_category_short_code_field.x_name + "/" + category.parent_id.parent_id.parent_id.x_studio_category_short_code_field.x_name + "/" + category.parent_id.parent_id.x_studio_category_short_code_field.x_name + "/" + category.parent_id.x_studio_category_short_code_field.x_name + "/" + category.x_studio_category_short_code_field.x_name
            elif counter == 3:
                mad_seq = category.parent_id.parent_id.parent_id.x_studio_category_short_code_field.x_name + "/" + category.parent_id.parent_id.x_studio_category_short_code_field.x_name + "/" + category.parent_id.x_studio_category_short_code_field.x_name + "/" + category.x_studio_category_short_code_field.x_name
            elif counter == 2:
                mad_seq = category.parent_id.parent_id.x_studio_category_short_code_field.x_name + "/" + category.parent_id.x_studio_category_short_code_field.x_name + "/" + category.x_studio_category_short_code_field.x_name
            elif counter == 1:
                mad_seq = category.parent_id.x_studio_category_short_code_field.x_name + "/" + category.x_studio_category_short_code_field.x_name

            mad_seq = mad_seq + "/" + seq1

        return mad_seq
    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        if self.categ_id:
            self.default_code = self.getInternalNumber(self.categ_id.id)
            
class Madfox_BaseReport(models.TransientModel):
    _inherit = 'base.document.layout'
    company_registry = fields.Char(related='company_id.company_registry', readonly=True)

   



