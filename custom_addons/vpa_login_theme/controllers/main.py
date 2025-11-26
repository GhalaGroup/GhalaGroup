# -*- coding: utf-8 -*-
# Part of VPA Login Theme. See LICENSE file for full copyright and licensing details.

import base64
from odoo import http
from odoo.http import request


class LoginThemeController(http.Controller):

    @http.route('/vpa_login_theme/favicon', type='http', auth='public')
    def get_custom_favicon(self, **kwargs):
        """Serve custom favicon from active theme"""
        try:
            LoginThemeConfig = request.env['login.theme.config'].sudo()
            theme = LoginThemeConfig.search([('active', '=', True)], limit=1)

            if theme and theme.custom_favicon:
                # Return custom favicon
                favicon_data = base64.b64decode(theme.custom_favicon)
                return request.make_response(
                    favicon_data,
                    headers=[
                        ('Content-Type', 'image/x-icon'),
                        ('Cache-Control', 'public, max-age=86400'),
                    ]
                )
        except:
            pass

        # Fallback to default Odoo favicon
        return request.redirect('/web/static/img/favicon.ico')

    @http.route('/vpa_login_theme/company_logo', type='http', auth='public')
    def get_company_logo(self, **kwargs):
        """Serve the company logo from the active theme's company"""
        try:
            LoginThemeConfig = request.env['login.theme.config'].sudo()
            theme = LoginThemeConfig.search([('active', '=', True)], limit=1)

            if theme and theme.company_id and theme.company_id.logo_web:
                # Return the company's logo
                logo_data = base64.b64decode(theme.company_id.logo_web)
                return request.make_response(
                    logo_data,
                    headers=[
                        ('Content-Type', 'image/png'),
                        ('Cache-Control', 'public, max-age=3600'),
                    ]
                )
        except Exception as e:
            pass

        # Fallback to default company logo
        try:
            company = request.env['res.company'].sudo().search([], limit=1)
            if company and company.logo_web:
                logo_data = base64.b64decode(company.logo_web)
                return request.make_response(
                    logo_data,
                    headers=[
                        ('Content-Type', 'image/png'),
                        ('Cache-Control', 'public, max-age=3600'),
                    ]
                )
        except:
            pass

        # Final fallback - redirect to Odoo default
        return request.redirect('/web/static/img/logo.png')

    @http.route('/vpa_login_theme/get_theme_css', type='http', auth='public')
    def get_theme_css(self, **kwargs):
        """Generate dynamic CSS based on theme configuration"""
        try:
            LoginThemeConfig = request.env['login.theme.config'].sudo()
            theme = LoginThemeConfig.get_active_theme()
        except:
            # Fallback to default red theme if database query fails
            theme = {
                'primary_color': '#DC143C',
                'secondary_color': '#B22222',
                'link_color': '#DC143C',
                'background_color': '#F3F4F6',
                'logo_max_height': 120,
                'logo_max_width': 100,
            }

        css_content = f"""
/* VPA Login Theme - Dynamic CSS */
/* Works with both light and dark themes */

/* Login Button Styling */
.oe_login_form .btn-primary {{
    background-color: {theme['primary_color']} !important;
    border-color: {theme['primary_color']} !important;
}}

.oe_login_form .btn-primary:hover {{
    background-color: {theme['secondary_color']} !important;
    border-color: {theme['secondary_color']} !important;
}}

.oe_login_form .btn-primary:focus,
.oe_login_form .btn-primary:active {{
    background-color: {theme['secondary_color']} !important;
    border-color: {theme['secondary_color']} !important;
    box-shadow: 0 0 0 0.2rem {theme['primary_color']}80 !important;
}}

/* Link Styling */
.oe_login_form a {{
    color: {theme['link_color']};
}}

.oe_login_form a:hover {{
    color: {theme['secondary_color']};
}}

/* Background - Light Theme */
body.bg-100 {{
    background-color: {theme['background_color']} !important;
}}

/* Background - Dark Theme Compatibility */
body[data-color-scheme="dark"].bg-100,
body.o_dark.bg-100 {{
    background-color: {theme['background_color']} !important;
}}

/* Logo Sizing */
.o_database_list img[alt="Logo"] {{
    max-height: {theme['logo_max_height']}px !important;
    max-width: {theme['logo_max_width']}% !important;
    width: auto;
}}

/* Card styling for dark theme compatibility */
body[data-color-scheme="dark"] .card,
body.o_dark .card {{
    background-color: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.1);
}}

/* Input fields dark theme */
body[data-color-scheme="dark"] .form-control,
body.o_dark .form-control {{
    background-color: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.2);
    color: #fff;
}}

body[data-color-scheme="dark"] .form-control:focus,
body.o_dark .form-control:focus {{
    background-color: rgba(255, 255, 255, 0.08);
    border-color: {theme['primary_color']};
    color: #fff;
}}

/* Text color adjustments for dark theme */
body[data-color-scheme="dark"] .text-muted,
body.o_dark .text-muted {{
    color: rgba(255, 255, 255, 0.6) !important;
}}
"""
        return request.make_response(
            css_content,
            headers=[
                ('Content-Type', 'text/css'),
                ('Cache-Control', 'public, max-age=3600'),
            ]
        )
