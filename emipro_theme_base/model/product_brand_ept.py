# -*- coding: utf-8 -*-
"""
    This model is used to create a product brand fields
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProductBrandEpt(models.Model):
    _name = 'product.brand.ept'
    _inherit = ['website.published.multi.mixin']
    _order = 'name'
    _description = 'Product Brand'

    name = fields.Char('Brand Name', required=True, translate=True)
    description = fields.Text('Description', translate=True)
    website_id = fields.Many2one("website", string="Website")
    logo = fields.Binary('Logo File')
    product_ids = fields.One2many('product.template', 'product_brand_ept_id', string="Products", readonly=True)
    products_count = fields.Integer(
        string='Number of products',
        compute='_compute_products_count',
        help='It shows the number of product counts',
    )
    is_brand_page = fields.Boolean(string='Is Brand Page',help="It will set the separate landing page for this brand")
    brand_page = fields.Many2one("website.page", string="Brand Page",help="Select the brand page which you want to set for this brand.")
    is_featured_brand = fields.Boolean(string='Is Featured Brand')
    allow_in_brand_slider = fields.Boolean(string='Allow In Brand Slider',
                                           help="You can set this brand in Brand carousel snippets.")

    @api.constrains('allow_in_brand_slider')
    def validate_brand_carousel(self):
        if not self.logo and self.allow_in_brand_slider:
            raise ValidationError(_("Please set the brand image before set this in carousel"))

    @api.depends('product_ids')
    def _compute_products_count(self):
        for brand in self:
            brand.products_count = len(brand.product_ids)

    def set_brand_wizard(self):
        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'product.brand.config',
            'name': "Product Brand Configuration",
            'view_mode': 'form',
            'target': 'new',
            'context': dict(default_brand_id=self.id),
        }
        return action