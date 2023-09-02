# -*- coding: utf-8 -*-

from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSale
from datetime import timedelta
import datetime
from odoo.http import request
from odoo import http
from odoo.tools.safe_eval import safe_eval


class SliderBuilder(WebsiteSale):

    # Render the Product while Editing the slider
    @http.route('/get-products-of-slider', type='json', auth='public', website=True)
    def get_products_of_slider(self, **kw):
        product_ids = kw.get('product_ids')
        if product_ids:
            products = request.env['product.template'].browse(product_ids).filtered(lambda r:r.exists() and r.sale_ok and r.website_published and r.website_id.id in (False, request.website.id) and r.type in ['product','consu'])
            products = [[product.id, product.name] for product in products if product]
            return products

    # Render the sldier popup
    @http.route('/get-slider-template', type='json', auth='public', website=True)
    def get_slider_template(self, **kw):
        tmplt = request.env['ir.ui.view'].sudo().search([('key', '=', 'emipro_theme_base.product_configure_template')])
        filters = request.env['slider.filter'].sudo().search([('website_published','=',True),('filter_domain','!=',False)])
        if tmplt:
            response = http.Response(template='emipro_theme_base.product_configure_template',qcontext = {'filters':filters})
            return response.render()

    # Return Suggested Products
    @http.route('/get-suggested-products', type='json', auth='public', website=True)
    def get_suggested_products(self, **kw):
        key = kw.get('key')
        exclude_products = kw.get('exclude_products')
        website_domain = request.website.website_domain()
        products = request.env['product.template'].search([('id', 'not in', exclude_products), ('sale_ok', '=', True),('name', 'ilike', key),('type','in',['product','consu'])]+website_domain,
                                                          limit=10)
        products = [[product.id, product.name] for product in products if product]
        return products

    @http.route('/get-first-product', type='json', auth='public', website=True)
    def get_products(self, **kw):
        styles = request.env['slider.styles'].search([('slider_type', '=', 'product'),('style_template_key','!=',False)])
        values = {
            'website': request.env['website'].sudo().get_current_website(),
            'styles': styles,
        }
        response = http.Response(template="emipro_theme_base.product_ui_configure_template",qcontext=values)
        return response.render()

    @http.route('/get-product-slider-template', type='json', auth='public', website=True)
    def get_product_slider_template(self, template=False):
        product = request.env['product.template'].search(
            [('sale_ok', '=', True), ('website_published', '=', True), ('type', '!=', 'service')], limit=1)
        styles = request.env['slider.styles'].search([('slider_type', '=', 'product'),('style_template_key','!=',False)])
        values = {
            'filter_data': product,
            'website': request.env['website'].sudo().get_current_website(),
            'option':['shopping_cart','wishlist','quick_view','sale_label'],
            'styles': styles,
        }
        if template:
            response = http.Response(template=template, qcontext=values)
            return response.render()

    # Render the slider data
    @http.route(['/slider/render'], type='json', auth="public", website=True)
    def slider_data(self, **kwargs):
        product_ids = kwargs.get('product_ids', False)
        product_ids = [int(i) for i in product_ids.split(',')] if product_ids else False
        selected_ui_options = kwargs.get('selected_ui_options', False)
        selected_ui_options = [i for i in selected_ui_options.split(',')] if selected_ui_options else False
        slider_style_template = kwargs.get('slider_style_template', False)
        slider_style_template = int(slider_style_template) if slider_style_template else False
        name = kwargs.get('name', False)
        discount_policy = kwargs.get('discount_policy',False)
        category_ids = kwargs.get('category_ids', False)
        category_ids = [int(i) for i in category_ids.split(',')] if category_ids else False
        filter_id = kwargs.get('filter_id', False)
        filter_id = int(filter_id) if filter_id else False
        limit = kwargs.get('limit', False)
        limit = int(limit) if limit else 10
        sort_by = kwargs.get('sort_by', 'name asc')
        products = []

        if name and slider_style_template:
            slider_style = request.env['slider.styles'].sudo().browse(slider_style_template).filtered(lambda r:r.exists())
            vals = {
                'option': selected_ui_options or [],
            }
            if name == 'manual-configuration' and product_ids:
                products = request.env['product.template'].browse(product_ids).filtered(lambda r:r.exists())
                products = products.filtered(lambda r: r.sale_ok and r.website_published and r.website_id.id in (
                False, request.website.id) and r.type in ['product', 'consu'])
            elif name == 'new-arrival':
                products = self.new_arrival_products(limit)
            elif name == 'custom-domain':
                products = self.custom_domain_products(filter_id,limit,sort_by)
            elif name == 'best-seller':
                products = self.best_seller_products(limit)
            elif name == 'product-discount':
                products = self.discounted_products('product',limit)
            elif name == 'product-category-discount' and category_ids:
                products = self.discounted_products('category',category_ids,discount_policy,limit)
            if products and slider_style:
                vals['filter_data'] = products
                if request.env['ir.ui.view'].sudo().search([('key', '=', request.website.sudo().theme_id.name+'.'+slider_style.style_template_key)]):
                    response = http.Response(template=request.website.sudo().theme_id.name+'.'+slider_style.style_template_key, qcontext=vals)
                    return response.render()
        # If no product found then render the error message template
        if request.env['ir.ui.view'].sudo().search(
                [('key', '=',request.website.sudo().theme_id.name + '.'+'slider_error_message')]):
            response = http.Response(template=request.website.sudo().theme_id.name+'.'+ 'slider_error_message')
            return response.render()

    # Return the products as per filter, limit and sorting option
    def custom_domain_products(self,filter_id,limit=10,sort_by='name asc'):
        filter_id = request.env['slider.filter'].sudo().browse(filter_id).filtered(lambda r:r.exists())
        if filter_id and filter_id.website_published:
            domain = safe_eval(filter_id.filter_domain)
            domain += ['|', ('website_id', '=', None), ('website_id', '=', request.website.id),
                       ('website_published', '=', True),('type','in',['product','consu']),('sale_ok','=',True)]
            return request.env['product.template'].sudo().search(domain,limit=limit,order=sort_by)

    # return the newly created products
    def new_arrival_products(self,limit=10):
        domain = request.website.sale_product_domain()
        domain += ['|', ('website_id', '=', None), ('website_id', '=', request.website.id),
                   ('website_published', '=', True),('type','in',['product','consu'])]
        return request.env['product.template'].sudo().search(domain, limit=limit,order='id desc')

    # Return the most selling product in last 8 days
    def best_seller_products(self,limit=10):
        website_id = request.website.id
        request.env.cr.execute("""select * from sale_report where website_id=%s AND state in ('sale','done') AND date BETWEEN %s and %s
                                                """,
                               (website_id, datetime.datetime.today() - timedelta(8), datetime.datetime.today()))
        sale_report_ids = [x[0] for x in request.env.cr.fetchall()]
        products = request.env['sale.report'].sudo().browse(sale_report_ids).mapped('product_tmpl_id')
        products = products.filtered(lambda r: r.website_published and r.sale_ok and r.website_id.id in (
            False, website_id) and r.type != 'service')[:limit]
        return products

    # Return the discounted product based on the current pricelist for category and product discount option selection
    def discounted_products(self, applied_on=False,category_ids = False,discount_policy=False,limit=10):
        price_list = request.website.get_current_pricelist()
        pl_items = price_list.item_ids.filtered(lambda r: r.applied_on == '1_product' and (
                (not r.date_start or r.date_start <= datetime.datetime.today()) and (
                not r.date_end or r.date_end > datetime.datetime.today())))
        if applied_on == 'product':
            return pl_items.mapped('product_tmpl_id').filtered(
                lambda r: r.sale_ok and r.website_published and r.website_id.id in (False, request.website.id) and r.type in ['product','consu'])[:limit]
        elif applied_on == 'category' and discount_policy == 'discounts':
            return pl_items.mapped('product_tmpl_id').filtered(lambda r: r.sale_ok and r.website_published and r.website_id.id in (False, request.website.id) and r.type in ['product','consu'] and [i for i in category_ids if i in r.public_categ_ids.ids])[:limit]
        else:
            domain = request.website.sale_product_domain()
            domain += ['|', ('website_id', '=', None), ('website_id', '=', request.website.id),
                       ('website_published', '=', True),('public_categ_ids','in',category_ids),('type','in',['product','consu'])]
            return request.env['product.template'].sudo().search(domain, limit=limit)
