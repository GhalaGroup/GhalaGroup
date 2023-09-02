# -*- coding: utf-8 -*-
"""
    This model is used to add a image field in attributes line
"""

from odoo import fields, models

class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    icon = fields.Image(string='Icon')
