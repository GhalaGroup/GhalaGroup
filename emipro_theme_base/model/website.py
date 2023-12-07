# -*- coding: utf-8 -*-

import json

import werkzeug.urls
import werkzeug.utils
from datetime import timedelta, date
from odoo.http import request
from odoo.tools import image_process
from werkzeug.exceptions import NotFound
from odoo.tools.safe_eval import safe_eval

import odoo
from odoo import fields, models, http
from odoo.addons.auth_oauth.controllers.main import OAuthLogin
from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSale
from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSaleWishlist
from odoo.addons.emipro_theme_base.controller.main import EmiproThemeBaseExtended


class Website(models.Model):
    _inherit = "website"

    def _get_default_header_content(self):
        return """
            <p></p>
            <div class="s_rating row te_s_header_offer_text">
            <ul>
                <li>Special Offer on First Purchase</li>
                <li>
                    <section>|</section>
                </li>
                <li>Code : #ASDA44</li>
                <li>
                    <section>|</section>
                </li>
                <li>Get 50% Off</li>
            </ul>
            </div>
            """

    def _get_default_footer_extra_links(self):
        return """
        <section>
        <div class="te_footer_inline_menu">
            <ul class="te_footer_inline_menu_t">
                <li>
                    <section>
                        <a href="#">About Us</a>
                    </section>
                </li>
                <li>
                    <section>
                        <a href="#">Contact Us</a>
                    </section>
                </li>
                <li>
                    <section>
                        <a href="#">Customer Service</a>
                    </section>
                </li>
                <li>
                    <section>
                        <a href="#">Privacy Policy</a>
                    </section>
                </li>
                <li>
                    <section>
                        <a href="#">Accessibility</a>
                    </section>
                </li>
                <li>
                    <section>
                        <a href="#">Store Directory</a>
                    </section>
                </li>
            </ul>
        </section>
        </div>
        """

    def _get_default_footer_content(self):
        return """
            <p></p>
            <div class="row">
                <div class="col-lg-4 col-md-4 col-6">
                    <ul class="te_footer_info_ept">
                        <section>
                            <li>
                                <a href="#">Help</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Gift Cards</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Order Status</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Free Shipping</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Returns Exchanges</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">International</a>
                            </li>
                        </section>
                    </ul>
                </div>
                <div class="col-lg-4 col-md-4 col-6">
                    <ul class="te_footer_info_ept">
                        <section>
                            <li>
                                <a href="#">About Us</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Jobs</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Affiliates</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Meet The Maker</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Contact</a>
                            </li>
                        </section>
                    </ul>
                </div>
                <div class="col-lg-4 col-md-4 col-6">
                    <ul class="te_footer_info_ept">
                        <section>
                            <li>
                                <a href="#">Security</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Privacy</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Text Messaging</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Legal</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Supply Chain</a>
                            </li>
                        </section>
                    </ul>
                </div>
            </div>
        """

    def _get_footer_style_3_content(self):
        return """
                <p></p>
                <section>
                    <div>
                        <h4 class="te_footer_menu_info">Informations</h4>
                    </div>
                </section>
                <div class="row">
                    <div class="col-lg-6 col-md-6 col-6">
                        <ul class="te_footer_info_ept">
                            <section>
                                <li>
                                    <a href="#">Help</a>
                                </li>
                            </section>


                            <section>
                                <li>
                                    <a href="#">Gift Cards</a>
                                </li>
                            </section>

                            <section>
                                <li>
                                    <a href="#">Order Status</a>
                                </li>
                            </section>
                            <section>
                                <li>
                                    <a href="#">Free Shipping</a>
                                </li>
                            </section>
                            <section>
                                <li>
                                    <a href="#">Returns Exchanges</a>
                                </li>
                            </section>
                            <section>
                                <li>
                                    <a href="#">International</a>
                                </li>
                            </section>
                        </ul>
                    </div>
                    <div class="col-lg-6 col-md-6 col-6">
                        <ul class="te_footer_info_ept">

                            <section>
                                <li>
                                    <a href="#">Security</a>
                                </li>
                            </section>
                            <section>
                                <li>
                                    <a href="#">Privacy</a>
                                </li>
                            </section>
                            <section>
                                <li>
                                    <a href="#">Text Messaging</a>
                                </li>
                            </section>
                            <section>
                                <li>
                                    <a href="#">Legal</a>
                                </li>
                            </section>
                            <section>
                                <li>
                                    <a href="#">Supply Chain</a>
                                </li>
                            </section>
                            <section>
                                <li>
                                    <a href="#">Contact</a>
                                </li>
                            </section>
                        </ul>
                    </div>
                </div>"""
    def _get_footer_style_4_content(self):
        return """
         <p></p>
            <div class="row">
                <div class="footer-column-2 col-md-3 col-sm-6">
                    <div class="footer_top_title_div">
                        <h5 class="footer-sub-title">Our Stores</h5>
                        <span>
                            <span class="fa fa-angle-down"></span>
                        </span>
                    </div>
                    <ul class="te_footer_info_ept">
                        <section>
                            <li>
                                <a href="#">New York</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">London SF</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Cockfosters BP</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Los Angeles</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Chicago</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Las Vegas</a>
                            </li>
                        </section>
                    </ul>
                </div>
                <div class="footer-column-2 col-md-3 col-sm-6">
                    <div class="footer_top_title_div">
                        <h5 class="footer-sub-title">Information</h5>
                        <span>
                            <span class="fa fa-angle-down"></span>
                        </span>
                    </div>
                    <ul class="te_footer_info_ept">
                        <section>
                            <li>
                                <a href="#">About Store</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">New Collection</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Woman Dress</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Contact Us</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Latest News</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Our Sitemap</a>
                            </li>
                        </section>
                    </ul>
                </div>
                <div class="footer-column-2 col-md-3 col-sm-6">
                    <div class="footer_top_title_div">
                        <h5 class="footer-sub-title">Useful links</h5>
                        <span>
                            <span class="fa fa-angle-down"></span>
                        </span>
                    </div>
                    <ul class="te_footer_info_ept">
                        <section>
                            <li>
                                <a href="#">Privacy Policy</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Returns</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Terms &amp; Conditions</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Contact Us</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Latest News</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Our Sitemap</a>
                            </li>
                        </section>
                    </ul>
                </div>
                <div class="footer-column-2 col-md-3 col-sm-6">
                    <div class="footer_top_title_div">
                        <h5 class="footer-sub-title">Footer Menu</h5>
                        <span>
                            <span class="fa fa-angle-down"></span>
                        </span>
                    </div>
                    <ul class="te_footer_info_ept">
                        <section>
                            <li>
                                <a href="#">Instagram profile</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">New Collection</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Woman Dress</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Contact Us</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Latest News</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Purchase Theme</a>
                            </li>
                        </section>
                    </ul>
                </div>
            </div>
        """
    def _get_footer_style_5_content(self):
        return """
        <p></p>
            <div class="row">
                <div class="col-sm-6">
                    <h3 class="te_block_title">My Account</h3>
                    <a class="te_collapse_icon collapsed" data-toggle="collapse" data-target="#my_account">
                        <div class="te_block_title_col">My Account</div>
                        <i class="fa fa-plus"></i>
                    </a>
                    <ul class="te_footer_info_ept collapse" id="my_account">
                        <section>
                            <li>
                                <a href="#">About Us</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Contact Us</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">My Account</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Order history</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Advanced search</a>
                            </li>
                        </section>
                    </ul>
                </div>
                <div class="col-sm-6">
                    <h3 class="te_block_title">Main Features</h3>
                    <a class="te_collapse_icon collapsed" data-toggle="collapse" data-target="#feature">
                        <div class="te_block_title_col">Main Features</div>
                        <i class="fa fa-plus"></i>
                    </a>
                    <ul class="te_footer_info_ept collapse" id="feature">
                        <section>
                            <li>
                                <a href="#">Lorem ipsum sit</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Lorem ipsum dolor amet</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Lorem ipsum amet</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Lorem ipsum dolor</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="#">Lorem ipsum sit</a>
                            </li>
                        </section>
                    </ul>
                </div>
            </div>
        """
    def _get_footer_style_6_content(self):
        return """
        <p></p>
        <div class="row">
            <div class="col-sm-6 col-6 te_account_info">
                <h3 class="te_block_title">My Account</h3>
                <ul class="te_footer_info_ept">
                    <section>
                        <li>
                            <a href="#">Help</a>
                        </li>
                    </section>
                    <section>
                        <li>
                            <a href="#">Gift Cards</a>
                        </li>
                    </section>
                    <section>
                        <li>
                            <a href="#">Order Status</a>
                        </li>
                    </section>
                    <section>
                        <li>
                            <a href="#">Free Shipping</a>
                        </li>
                    </section>
                    <section>
                        <li>
                            <a href="#">Returns Exchanges</a>
                        </li>
                    </section>
                    <section>
                        <li>
                            <a href="#">International</a>
                        </li>
                    </section>
                </ul>
            </div>
            <div class="col-sm-6 col-6">
                <h3 class="te_block_title">Main Features</h3>
                <ul class="te_footer_info_ept">
                    <section>
                        <li>
                            <a href="#">About Us</a>
                        </li>
                    </section>
                    <section>
                        <li>
                            <a href="#">Jobs</a>
                        </li>
                    </section>
                    <section>
                        <li>
                            <a href="#">Affiliates</a>
                        </li>
                    </section>
                    <section>
                        <li>
                            <a href="#">Meet The Maker</a>
                        </li>
                    </section>
                    <section>
                        <li>
                            <a href="#">Contact</a>
                        </li>
                    </section>
                </ul>
            </div>
        </div>
        """

    def _get_footer_style_7_content(self):
        return """
            <p></p>
            <div class="row">
                <div class="col-md-6 col-6">
                    <h3 class="te_block_title">Useful link</h3>
                    <ul class="te_footer_info_ept">
                        <section>
                            <li>
                                <i class="fa fa-long-arrow-right"></i>
                                <a href="#">Help</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <i class="fa fa-long-arrow-right"></i>
                                <a href="#">Gift Cards</a>
                            </li>
                        </section>
            
                        <section>
                            <li>
                                <i class="fa fa-long-arrow-right"></i>
                                <a href="#">Order Status</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <i class="fa fa-long-arrow-right"></i>
                                <a href="#">Free Shipping</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <i class="fa fa-long-arrow-right"></i>
                                <a href="#">Returns Exchanges</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <i class="fa fa-long-arrow-right"></i>
                                <a href="#">International</a>
                            </li>
                        </section>
                    </ul>
                </div>
                <div class="col-md-6 col-6">
                    <h3 class="te_block_title">Take Action</h3>
                    <ul class="te_footer_info_ept">
                        <section>
                            <li>
                                <i class="fa fa-long-arrow-right"></i>
                                <a href="#">Security</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <i class="fa fa-long-arrow-right"></i>
                                <a href="#">Privacy</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <i class="fa fa-long-arrow-right"></i>
                                <a href="#">Text Messaging</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <i class="fa fa-long-arrow-right"></i>
                                <a href="#">Legal</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <i class="fa fa-long-arrow-right"></i>
                                <a href="#">Supply Chain</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <i class="fa fa-long-arrow-right"></i>
                                <a href="#">Contact</a>
                            </li>
                        </section>
                    </ul>
                </div>
            </div>
        """
    def _get_default_header_extra_links(self):
        return """
            <p></p>
            <div class="te_header_static_menu">
                <ul>
                    <li>
                        <a href="#">Custom menu</a>
                    </li>
                    <li>
                        <a href="#">Information</a>
                    </li>
                    <li>
                        <a href="#">About us</a>
                    </li>
                    <li>
                        <a href="#">Our story</a>
                    </li>
                </ul>
            </div>
        """
    def _get_default_vertical_menu(self):
        return """
            <section>
                <div class="te_sidenav_menu">
                    <ul>
                        <section>
                            <li>
                                <a href="/shop">About Shop</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="/contactus">Help Center</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="/aboutus">Portfolio</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="/blog">Blog</a>
                            </li>
                        </section>
                        <section>
                            <li>
                                <a href="/shop">New Look</a>
                            </li>
                        </section>
                    </ul>
                </div>
                <div class="te_sidenav_content">
                    <section>
                        <p>Pellentesque mollis nec orci id tincidunt. Sed mollis risus eu nisi aliquet, sit amet
                            fermentum.
                        </p>
                    </section>
                </div>
            </section>
        """

    def _get_default_facebook(self):
        return """
            <span class="fa fa-facebook"/>
        """
    def _get_default_twitter(self):
        return """
            <span class="fa fa-twitter"/>
        """
    def _get_default_linkedin(self):
        return """    
            <span class="fa fa-linkedin"/>
        """
    def _get_default_youtube(self):
        return """    
            <span class="fa fa-youtube-play"/>
        """
    def _get_default_github(self):
        return """    
            <span class="fa fa-github"/>
        """
    def _get_default_instagram(self):
        return """    
            <span class="fa fa-instagram"/>
        """

    facebook_sharing = fields.Boolean(string='Facebook')
    twitter_sharing = fields.Boolean(string='Twitter')
    linkedin_sharing = fields.Boolean(string='Linkedin')
    mail_sharing = fields.Boolean(string='Mail')
    is_load_more = fields.Boolean(string='Load More', help="Load more will be enabled", readonly=False)
    load_more_image = fields.Binary('Load More Image', help="Display this image while load more applies.",
                                    readonly=False)
    button_or_scroll = fields.Selection([
        ('automatic', 'Automatic- on page scroll'),
        ('button', 'Button- on click button')
    ], string="Loading type for products",
        required=True, default='automatic', readonly=False)
    prev_button_label = fields.Char(string='Label for the Prev Button', readonly=False,
                                    default="Load prev", translate=True)
    next_button_label = fields.Char(string='Label for the Next Button', readonly=False,
                                    default="Load next", translate=True)
    is_lazy_load = fields.Boolean(string='Lazyload', help="Lazy load will be enabled", readonly=False)
    lazy_load_image = fields.Binary('Lazyload Image', help="Display this image while lazy load applies.",
                                    readonly=False)
    banner_video_url = fields.Many2one('ir.attachment', "Video URL", help='URL of a video for banner.', readonly=False)
    number_of_product_line = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3')
    ], string="Number of lines for product name", default='1', readonly=False, help="Number of lines to show in product name for shop.")
    website_company_info = fields.Text(string="Company Information", translate=True,
                                       default="We are a team of passionate people whose goal is to improve "
                                               "everyone's life through disruptive products. We build great products to solve your business problems.")
    website_footer_extra_links = fields.Html(string="Footer Content", translate=True,
                                             default=_get_default_footer_extra_links)
    website_header_offer_ept = fields.Html(string="Clarico Header Offer Content", translate=True,sanitize=False,
                                           default=_get_default_header_content)
    footer_style_1_content_ept = fields.Html(string="Clarico Footer Style 1 Content", translate=True,sanitize=False,
                                             default=_get_default_footer_content)
    footer_style_3_content_ept = fields.Html(string="Clarico Footer Style 3 Content", translate=True,sanitize=False,
                                             default=_get_footer_style_3_content)
    footer_style_4_content_ept = fields.Html(string="Clarico Footer Style 4 Content", translate=True,sanitize=False,
                                             default=_get_footer_style_4_content)
    footer_style_5_content_ept = fields.Html(string="Clarico Footer Style 5 Content", translate=True,sanitize=False,
                                             default=_get_footer_style_5_content)
    footer_style_6_content_ept = fields.Html(string="Clarico Footer Style 6 Content", translate=True, sanitize=False,
                                             default=_get_footer_style_6_content)
    footer_style_7_content_ept = fields.Html(string="Clarico Footer Style 7 Content", translate=True, sanitize=False,
                                             default=_get_footer_style_7_content)
    website_header_extra_links = fields.Html(string="Clarico Header Extra Content", translate=True, sanitize=False,
                                           default=_get_default_header_extra_links)
    website_vertical_menu_ept = fields.Html(string="Vertical Menu Content", translate=True, sanitize=False,
                                           default=_get_default_vertical_menu)
    is_auto_play = fields.Boolean(string='Slider Auto Play', default=True, readonly=False)

    is_pwa = fields.Boolean(string='PWA', readonly=False, help="Pwa will be enabled.")
    pwa_name = fields.Char(string='Name', readonly=False)
    pwa_short_name = fields.Char(string='Short Name', readonly=False)
    pwa_theme_color = fields.Char(string='Theme Color', readonly=False)
    pwa_bg_color = fields.Char(string='Background Color', readonly=False)
    pwa_start_url = fields.Char(string='Start URL', readonly=False)
    app_image_512 = fields.Binary(string='Application Image(512x512)', readonly=False, store=True)
    is_price_range_filter = fields.Boolean(string='Price Range Filter',help="Enable the price range filter")
    price_filter_on = fields.Selection([
        ('list_price', 'On Product Sale Price'),
        ('website_price', 'On Product Discount Price')
    ], string="Price Range Filter For Products",
         default='list_price', readonly=False)

    # @api.depends('banner_video_url')
    # def _compute_embed_code(self):
    #     for image in self:
    #         image.embed_code = get_video_embed_code(image.video_url)

    def getDatabase(self):
        """
                To display database in login popup
                :return: List of databases
                """
        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None
        return values['databases']

    def category_check(self):
        """
        To display main parent product.public.category website specific
        :return:
        """
        return self.env['product.public.category'].sudo().search(
            [('parent_id', '=', False), ('website_id', 'in', (False, self.id))])

    def get_default_company_address(self):
        """
        To get company default address
        :return:
        """
        street = ''
        street2 = ''
        city = ''
        zip = ''
        state = ''
        country = ''

        getCurrentCompany = request.env['website'].get_current_website().company_id

        values = {
            'street': getCurrentCompany.street,
            'street2': getCurrentCompany.street2,
            'city': getCurrentCompany.city,
            'zip': getCurrentCompany.zip,
            'state_id': getCurrentCompany.state_id.name,
            'country_id': getCurrentCompany.country_id.name
        }

        if getCurrentCompany.street:
            street = str(values['street'])
        if getCurrentCompany.street2:
            street2 = str(values['street2'])
        if getCurrentCompany.city:
            city = str(values['city'])
        if getCurrentCompany.zip:
            zip = values['zip']
        if getCurrentCompany.state_id.name:
            state = str(values['state_id'])
        if getCurrentCompany.country_id.name:
            country = str(values['country_id'])

        return street +' '+ street2 +' '+ city + ' '+ zip + ' '+ state + ' '+ country

    def get_brand(self, products=False):
        """
        This function is used to search the list of brand data
        :return: List of brand
        """

        shop_brands = self.env['product.brand.ept'].sudo().search([('website_published','=', True),('website_id', 'in', (False,self.get_current_website().id))]).filtered(lambda r:r.products_count > 0)
        return shop_brands

    def get_parent_category(self):
        """
        Collect all the parent category. and return with category name and category ID
        @Author : Angel Patel (24/09/2020)
        :return: cat_array
        """
        category_obj = self.env['product.public.category'].sudo().search([('parent_id', '=', False),('website_id','in',[False,request.env['website'].sudo().get_current_website().id])])
        cat_array = [{'name': "All",'id':""}]
        if category_obj:
            for cat in category_obj:
                cat_array.append({'name': cat.name, 'id': cat.id})
        return cat_array

    def get_product_categs_path(self, id):
        """
        To render full path for breadcrumbs based on argument
        :param id: product.public.category
        :return: list of category path and website url
        """
        categ_set = []
        categ_name_set = []
        if id:
            while id:
                categ = self.env['product.public.category'].sudo().search([('id', '=', id)])
                categ_set.append(categ.id)
                categ_name_set.append(categ.name)
                if categ and categ.parent_id:
                    id = categ.parent_id.id
                else:
                    break

        # For Reverse order
        categ_set = categ_set[::-1]
        categ_name_set = categ_name_set[::-1]

        values = {
            'categ_set': categ_set,
            'categ_name_set':categ_name_set,
            'web_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        }
        return values

    def get_min_max_prices(self, search=False, category=False, attributes=False):
        """
        Get minimum price and maximum price according to Price list as well as discount for Shop page
        :return: min and max price value
        """
        range_list = []
        cust_min_val = request.httprequest.values.get('min_price', False)
        cust_max_val = request.httprequest.values.get('max_price', False)
        domain = WebsiteSaleWishlist._get_search_domain(self, search=search, category=category,
                                                        attrib_values=attributes)

        if attributes:
            ids = [attrib[1] for attrib in attributes if attrib[0] == 0]
            if ids:
                domain += [('product_brand_ept_id.id', 'in', ids)]
        products = self.env['product.template'].search(domain)
        prices_list = []
        min_price = max_price = 0
        is_web_price = request.website.price_filter_on == 'website_price'
        if products:
            pricelist = self.get_current_pricelist()
            if is_web_price:
                context = dict(self.env.context, quantity=1, pricelist=pricelist.id if pricelist else False)
                products = products.with_context(context).sorted('price')
            else:
                products = products.sorted('lst_price')
                min_price = products[0].currency_id._convert(products[0].lst_price, pricelist.currency_id,
                                                              self.company_id, date=fields.Date.today())
                max_price = products[-1].currency_id._convert(products[-1].lst_price, pricelist.currency_id,
                                                              self.company_id, date=fields.Date.today())

        if not products : return False

        try:
            cust_max_val = float(cust_max_val)
        except ValueError:
            cust_max_val = max_price
        try:
            cust_min_val = float(cust_min_val)
        except ValueError:
            cust_min_val = min_price

        if not cust_min_val and not cust_max_val:
            range_list.append(round(products[0].price if is_web_price else min_price,2))
            range_list.append(round(products[-1].price if is_web_price else max_price,2))
            range_list.append(round(products[0].price if is_web_price else min_price, 2))
            range_list.append(round(products[-1].price if is_web_price else max_price, 2))
        else:
            range_list.append(round(float(cust_min_val),2))
            range_list.append(round(float(cust_max_val),2))
            range_list.append(round(products[0].price if is_web_price else min_price, 2))
            range_list.append(round(products[-1].price if is_web_price else max_price, 2))
        return range_list

    def image_resize(self, img, width, height):
        """
        This function is used for resize the image with specific height and width
        and return the resizable image.
        :param img: image url
        :param width: image width
        :param height: image height
        :return: resizable image url
        """
        return image_process(img, size=(width, height))

    def get_carousel_category_list(self):
        """
        This method is used for return the list of category
        which has selected the allow category in carousel option from admin
        :return: list of category.
        """
        domain = [('website_id', 'in', (False, self.get_current_website().id)),
                  ('allow_in_category_carousel', '=', True)]
        category = self.env['product.public.category'].sudo().search(domain)
        return category

    def checkQuickFilter(self, currentWebsite, filterWebsiteArray):
        if currentWebsite in filterWebsiteArray or len(filterWebsiteArray) == 0:
            return True
        else:
            return False

    def list_providers_ept(self):
        """
        This method is used for return the encoded url for the auth providers
        :return: link for the auth providers.
        """
        try:
            providers = request.env['auth.oauth.provider'].sudo().search_read([('enabled', '=', True)])
        except Exception:
            providers = []
        for provider in providers:
            return_url = request.httprequest.url_root + 'auth_oauth/signin'
            state = OAuthLogin.get_state(self, provider)
            params = dict(
                response_type='token',
                client_id=provider['client_id'],
                redirect_uri=return_url,
                scope=provider['scope'],
                state=json.dumps(state),
            )
            provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.url_encode(params))
        return providers


    def get_shop_products(self, search=False, category=False, attrib_values=False):
        """
        Get the product count based on attribute value and current search domain.
        """
        domain = EmiproThemeBaseExtended._get_search_domain(EmiproThemeBaseExtended(),search, category, attrib_values)
        prod = self.env['product.template']
        query = prod._where_calc(domain)
        prod._apply_ir_rules(query, 'read')
        from_clause, where_clause, where_clause_params = query.get_sql()
        where_str = where_clause and ("WHERE %s" % where_clause) or ''
        query_str = 'SELECT product_template.id FROM ' + from_clause + where_str
        self._cr.execute(query_str, where_clause_params)
        temp_ids = [m_dict['id'] for m_dict in request.env.cr.dictfetchall()]
        if not temp_ids:
            return {}
        temp_ids_data = "(%s)" % tuple(temp_ids) if len(temp_ids) == 1 else str(tuple(temp_ids))
        query_attrb = '''select product_attribute_value_id,count(DISTINCT product_tmpl_id) as count from product_template_attribute_value where ptav_active = true AND product_tmpl_id in %s group by product_attribute_value_id'''%temp_ids_data
        self._cr.execute(query_attrb)
        attribute_dict = {}
        for dict in request.env.cr.dictfetchall():
            attribute_dict[dict['product_attribute_value_id']]=dict['count']
        return attribute_dict

    def get_brand_products(self, search=False, category=False, attrib_values=False):
        """
        Get the product count based on attribute value and current search domain.
        """
        domain = EmiproThemeBaseExtended._get_search_domain(EmiproThemeBaseExtended(),search, category, attrib_values)
        prod = self.env['product.template']
        domain = [dom for dom in domain if not dom[0] == 'product_brand_ept_id.id']
        query = prod._where_calc(domain)
        prod._apply_ir_rules(query, 'read')
        from_clause, where_clause, where_clause_params = query.get_sql()
        where_str = where_clause and ("WHERE %s" % where_clause) or ''
        query_str = 'SELECT product_template.id FROM ' + from_clause + where_str
        self._cr.execute(query_str, where_clause_params)
        temp_ids = [m_dict['id'] for m_dict in request.env.cr.dictfetchall()]
        if not temp_ids:
            return {}
        temp_ids_data = "(%s)" % tuple(temp_ids) if len(temp_ids) == 1 else str(tuple(temp_ids))
        query_brand = '''select product_brand_ept_id,count(id) as count from product_template where id in %s group by product_brand_ept_id'''%temp_ids_data
        self._cr.execute(query_brand)
        brand_dict = {}
        for dict in request.env.cr.dictfetchall():
            brand_dict[dict['product_brand_ept_id']]=dict['count']
        return brand_dict

