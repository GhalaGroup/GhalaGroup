# -*- coding: utf-8 -*-
{
    # Theme information
    'name': 'Emipro Theme Base',
    'category': 'Base',
    'summary': 'Base module containing common libraries for all Emipro eCommerce themes.',
    'version': '2.2.0',
    'license': 'OPL-1',
    'depends': [
        'website_sale_wishlist',
        'website_sale_comparison',
        'website_blog',
    ],

    'data': [
        'data/slider_styles_data.xml',
        'templates/template.xml',
        'templates/slider_popup.xml',
        'templates/pwa.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'views/product_template.xml',
        'views/product_public_category.xml',
        'views/product_attribute_value_view.xml',
        'wizard/product_brand_wizard_view.xml',
    ],

    # Odoo Store Specific
    'images': [
        'static/description/emipro_theme_base.jpg',
    ],

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'https://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

    # Technical
    'installable': True,
    'auto_install': False,
    'price': 9.00,
    'currency': 'EUR',
}
