# -*- coding: utf-8 -*-
# Part of VPA Login Theme. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class LoginThemeConfig(models.Model):
    _name = 'login.theme.config'
    _description = 'Login Theme Configuration'
    _rec_name = 'theme_name'

    theme_name = fields.Char(string='Theme Name', required=True, default='Custom Theme')
    primary_color = fields.Char(
        string='Primary Color (Button)',
        required=True,
        default='#DC143C',
        help='Hex color code for the login button (e.g., #DC143C for red)'
    )
    secondary_color = fields.Char(
        string='Secondary Color (Hover)',
        required=True,
        default='#B22222',
        help='Hex color code for button hover effect'
    )
    link_color = fields.Char(
        string='Link Color',
        required=True,
        default='#DC143C',
        help='Hex color code for links on login page'
    )
    logo_max_height = fields.Integer(
        string='Logo Max Height (px)',
        default=120,
        help='Maximum height of the company logo in pixels'
    )
    logo_max_width = fields.Integer(
        string='Logo Max Width (%)',
        default=100,
        help='Maximum width of the company logo as percentage'
    )
    background_color = fields.Char(
        string='Background Color',
        default='#F3F4F6',
        help='Background color of the login page'
    )
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    login_company_id = fields.Many2one(
        'res.company',
        string='Login Page Company',
        help='Company whose logo will be displayed on the login page. If not set, uses the Company field above.',
        default=lambda self: self.env.company
    )

    # Branding & Text Settings
    page_title = fields.Char(
        string='Page Title',
        default='Odoo',
        help='Browser tab title for the login page'
    )
    welcome_message = fields.Text(
        string='Welcome Message',
        help='Custom message displayed above the login form'
    )
    footer_text = fields.Char(
        string='Footer Text',
        help='Custom footer text (e.g., copyright notice)'
    )

    # Visual Settings
    border_radius = fields.Integer(
        string='Border Radius (px)',
        default=4,
        help='Border radius for buttons and login box in pixels'
    )

    # Visibility Settings
    show_database_selector = fields.Boolean(
        string='Show Database Selector',
        default=True,
        help='Display database selection dropdown on login page'
    )

    # Preview Field
    preview_html = fields.Html(
        string='Preview',
        compute='_compute_preview_html',
        sanitize=False
    )

    # Company Logo Display (for preview)
    company_logo = fields.Binary(
        string='Company Logo',
        related='company_id.logo_web',
        readonly=True
    )

    # Custom Favicon
    custom_favicon = fields.Binary(
        string='Custom Favicon',
        attachment=True,
        help='Upload a custom favicon (.ico, .png). Recommended size: 16x16 or 32x32 pixels'
    )
    favicon_filename = fields.Char(string='Favicon Filename')

    # Preset theme selection
    preset_theme = fields.Selection([
        ('custom', 'Custom'),
        ('red', 'Red Theme'),
        ('blue', 'Blue Theme'),
        ('green', 'Green Theme'),
        ('purple', 'Purple (Odoo Default)'),
        ('orange', 'Orange Theme'),
        ('dark', 'Dark Theme'),
    ], string='Preset Theme', default='red')

    @api.onchange('preset_theme')
    def _onchange_preset_theme(self):
        """Apply preset theme colors"""
        themes = {
            'red': {
                'primary_color': '#DC143C',
                'secondary_color': '#B22222',
                'link_color': '#DC143C',
                'background_color': '#F3F4F6',
                'theme_name': 'Red Theme'
            },
            'blue': {
                'primary_color': '#1E40AF',
                'secondary_color': '#1E3A8A',
                'link_color': '#2563EB',
                'background_color': '#EFF6FF',
                'theme_name': 'Blue Theme'
            },
            'green': {
                'primary_color': '#059669',
                'secondary_color': '#047857',
                'link_color': '#10B981',
                'background_color': '#ECFDF5',
                'theme_name': 'Green Theme'
            },
            'purple': {
                'primary_color': '#7C3AED',
                'secondary_color': '#6D28D9',
                'link_color': '#8B5CF6',
                'background_color': '#F5F3FF',
                'theme_name': 'Purple Theme (Odoo Default)'
            },
            'orange': {
                'primary_color': '#EA580C',
                'secondary_color': '#C2410C',
                'link_color': '#F97316',
                'background_color': '#FFF7ED',
                'theme_name': 'Orange Theme'
            },
            'dark': {
                'primary_color': '#1F2937',
                'secondary_color': '#111827',
                'link_color': '#374151',
                'background_color': '#E5E7EB',
                'theme_name': 'Dark Theme'
            },
        }

        if self.preset_theme and self.preset_theme != 'custom':
            theme_data = themes.get(self.preset_theme, {})
            self.primary_color = theme_data.get('primary_color', self.primary_color)
            self.secondary_color = theme_data.get('secondary_color', self.secondary_color)
            self.link_color = theme_data.get('link_color', self.link_color)
            self.background_color = theme_data.get('background_color', self.background_color)
            self.theme_name = theme_data.get('theme_name', self.theme_name)

    @api.depends('primary_color', 'secondary_color', 'link_color', 'background_color', 'border_radius', 'logo_max_height', 'logo_max_width', 'page_title', 'welcome_message', 'footer_text', 'company_id')
    def _compute_preview_html(self):
        """Generate HTML preview of the login theme"""
        for record in self:
            # Get the actual company logo URL
            if record.company_id:
                company_logo_url = f'/web/image/res.company/{record.company_id.id}/logo_web'
            else:
                company_logo_url = '/web/static/img/logo.png'

            preview_html = f"""
            <div style="background-color: {record.background_color or '#F3F4F6'}; padding: 40px; border-radius: 8px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                <div style="max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <!-- Logo -->
                    <div style="text-align: center; margin-bottom: 24px;">
                        <img src="{company_logo_url}"
                             style="max-height: {record.logo_max_height or 120}px; max-width: {record.logo_max_width or 100}%; height: auto;"
                             alt="Company Logo"/>
                    </div>

                    <!-- Welcome Message -->
                    {f'<div style="text-align: center; margin-bottom: 20px; color: #374151; font-size: 14px;">{record.welcome_message}</div>' if record.welcome_message else ''}

                    <!-- Page Title Preview -->
                    <div style="text-align: center; margin-bottom: 20px; color: #6B7280; font-size: 12px;">
                        <i class="fa fa-window-maximize"></i> Browser Tab: <strong>{record.page_title or 'Odoo'}</strong>
                    </div>

                    <!-- Login Form Preview -->
                    <div style="margin-bottom: 16px;">
                        <input type="text" placeholder="Email" readonly
                               style="width: 100%; padding: 10px; border: 1px solid #D1D5DB; border-radius: {record.border_radius or 4}px; font-size: 14px; box-sizing: border-box;"/>
                    </div>

                    <div style="margin-bottom: 16px;">
                        <input type="password" placeholder="Password" readonly
                               style="width: 100%; padding: 10px; border: 1px solid #D1D5DB; border-radius: {record.border_radius or 4}px; font-size: 14px; box-sizing: border-box;"/>
                    </div>

                    <!-- Login Button Preview -->
                    <button type="button"
                            onmouseover="this.style.backgroundColor='{record.secondary_color or '#B22222'}'"
                            onmouseout="this.style.backgroundColor='{record.primary_color or '#DC143C'}'"
                            style="width: 100%; padding: 12px; background-color: {record.primary_color or '#DC143C'}; color: white; border: none; border-radius: {record.border_radius or 4}px; font-size: 16px; font-weight: 600; cursor: pointer; transition: background-color 0.3s ease; margin-bottom: 16px;">
                        Log in
                    </button>

                    <!-- Link Preview -->
                    <div style="text-align: center;">
                        <a href="#" style="color: {record.link_color or '#DC143C'}; text-decoration: none; font-size: 14px;">Reset Password</a>
                    </div>

                    <!-- Footer Preview -->
                    {f'<div style="text-align: center; margin-top: 24px; padding-top: 16px; border-top: 1px solid #E5E7EB; color: #6B7280; font-size: 12px;">{record.footer_text}</div>' if record.footer_text else ''}
                </div>

                <div style="text-align: center; margin-top: 20px; color: #6B7280; font-size: 12px;">
                    <i class="fa fa-info-circle"></i> This is a preview - hover over the button to see the hover color!
                </div>
            </div>
            """
            record.preview_html = preview_html

    @api.model
    def get_active_theme(self):
        """Get the active theme configuration"""
        active_theme = self.search([('active', '=', True), ('company_id', '=', self.env.company.id)], limit=1)
        if not active_theme:
            # Create default theme if none exists
            active_theme = self.create({
                'theme_name': 'Default Red Theme',
                'primary_color': '#DC143C',
                'secondary_color': '#B22222',
                'link_color': '#DC143C',
                'preset_theme': 'red',
            })
        return {
            'primary_color': active_theme.primary_color,
            'secondary_color': active_theme.secondary_color,
            'link_color': active_theme.link_color,
            'logo_max_height': active_theme.logo_max_height,
            'logo_max_width': active_theme.logo_max_width,
            'background_color': active_theme.background_color,
        }
