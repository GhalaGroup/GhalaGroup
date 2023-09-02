# -*- coding: utf-8 -*-
"""
    This model is used to create a quick filter boolean field and icon style for color type in attributes
"""

from odoo import fields, models


class ProductAttribute(models.Model):
    _inherit = ['product.attribute']
    
    is_quick_filter = fields.Boolean(string='Quick Filter', help="It will show this attribute in quick filter")
    website_ids = fields.Many2many('website', help="You can set the filter in particular website.")
    exclude_website_ids = fields.Many2many('website', 'website_exclude_rel', string="Hide from Product Filter", help="Exclude the Attribute from Product Filter listing as well as Quick Filter based on Website selection.")
    icon_style = fields.Selection(selection=[('round', "Round"), ('square', "Square"), ], string="Icon Style", default='round', help="Here, Icon size is 40*40")
  
