# -*- coding: utf-8 -*-
from odoo import models, fields, api


class VPADocumentConfig(models.Model):
    _name = 'vpa.document.config'
    _description = 'VPA Document Layout Configuration'

    class Constraint(models.Constraint):
        _constraint_name = 'company_uniq'
        _definition = 'unique(company_id)'
        _message = 'Only one VPA configuration per company is allowed!'

    name = fields.Char(string='Configuration Name', required=True, default='VPA Layout Config')
    company_id = fields.Many2one('res.company', string='Company', required=False, ondelete='cascade', default=lambda self: self.env.company)

    # Preview field (sanitize=False for iframe rendering)
    preview = fields.Html(compute='_compute_preview', sanitize=False)

    # ========== HEADER CONFIGURATION ==========
    # Logo Settings
    header_logo_position = fields.Selection([
        ('start', 'Left'),
        ('center', 'Center'),
        ('end', 'Right')
    ], string='Logo Position', default='end')
    header_logo_width = fields.Integer(string='Logo Width (px)', default=150)
    header_logo_height = fields.Integer(string='Logo Height (px)', default=50)

    # Header Layout
    header_show_tagline = fields.Boolean(string='Show Company Tagline', default=True)
    header_tagline_position = fields.Selection([
        ('start', 'Left'),
        ('center', 'Center'),
        ('end', 'Right')
    ], string='Tagline Position', default='start')

    # Header Shape/Background
    header_show_circle = fields.Boolean(string='Show Circle Shape', default=True)
    header_circle_size = fields.Integer(string='Circle Size', default=1100)
    header_circle_opacity = fields.Float(string='Circle Opacity', default=0.1, digits=(3, 2))
    header_circle_color = fields.Char(string='Circle Color (Override)', default='#875a7b', help='Leave empty to use company primary color')

    # Header Multi-Row Sections
    header_enable_custom_sections = fields.Boolean(string='Enable Custom Header Sections', default=False)
    header_section_1_content = fields.Html(string='Header Section 1 (Top Row)', help='HTML content for first header row')
    header_section_1_align = fields.Selection([
        ('start', 'Left'),
        ('center', 'Center'),
        ('end', 'Right'),
        ('justify', 'Justified')
    ], string='Section 1 Alignment', default='start')

    header_section_2_content = fields.Html(string='Header Section 2 (Middle Row)', help='HTML content for second header row')
    header_section_2_align = fields.Selection([
        ('start', 'Left'),
        ('center', 'Center'),
        ('end', 'Right'),
        ('justify', 'Justified')
    ], string='Section 2 Alignment', default='center')

    header_section_3_content = fields.Html(string='Header Section 3 (Bottom Row)', help='HTML content for third header row')
    header_section_3_align = fields.Selection([
        ('start', 'Left'),
        ('center', 'Center'),
        ('end', 'Right'),
        ('justify', 'Justified')
    ], string='Section 3 Alignment', default='end')

    # Company Details
    header_company_details_position = fields.Selection([
        ('start', 'Left'),
        ('center', 'Center'),
        ('end', 'Right')
    ], string='Company Details Position', default='end')
    header_company_details_html = fields.Html(string='Company Details Custom HTML',
        help='Edit this HTML to customize the styling of company details. Click "Load Company Details" button to populate from company settings.')
    header_show_vat = fields.Boolean(string='Show VAT/Tax ID', default=True)

    # ========== BODY CONFIGURATION ==========
    # Document Title
    body_title_position = fields.Selection([
        ('start', 'Left'),
        ('center', 'Center'),
        ('end', 'Right')
    ], string='Document Title Position', default='end')
    body_title_size = fields.Selection([
        ('small', 'Small (h3)'),
        ('medium', 'Medium (h2)'),
        ('large', 'Large (h1)')
    ], string='Document Title Size', default='medium')

    # Table Styling
    body_table_style = fields.Selection([
        ('boxed-rounded', 'Boxed with Rounded Corners'),
        ('striped', 'Striped Rows'),
        ('bordered', 'Full Borders'),
        ('minimal', 'Minimal')
    ], string='Table Style', default='boxed-rounded')
    body_table_header_bg = fields.Char(string='Table Header Background', default='#f8f9fa')
    body_table_border_color = fields.Char(string='Table Border Color', default='#dee2e6')

    # Customer Address
    body_show_customer_address = fields.Boolean(string='Show Customer Address', default=True)
    body_customer_address_position = fields.Selection([
        ('left', 'Left'),  # Keep 'left' and 'right' for this field as it controls column position
        ('right', 'Right')
    ], string='Customer Address Position', default='left')

    # ========== FOOTER CONFIGURATION ==========
    # Footer Layout
    footer_layout = fields.Selection([
        ('centered', 'Centered (All content in center)'),
        ('split', 'Split (Bank left, Page right)'),
        ('custom', 'Custom Multi-Row Sections')
    ], string='Footer Layout', default='custom')

    # Footer Shape/Background
    footer_show_shape = fields.Boolean(string='Show Footer Shape', default=True)
    footer_shape_opacity = fields.Float(string='Footer Shape Opacity', default=0.1, digits=(3, 2))
    footer_shape_color = fields.Char(string='Footer Shape Color (Override)', default='#21b799', help='Leave empty to use company secondary color')

    # Footer Multi-Row Sections (3 rows for detailed information)
    footer_enable_custom_sections = fields.Boolean(string='Enable Custom Footer Sections', default=True)

    # Row 1: Company Information
    footer_row1_enable = fields.Boolean(string='Enable Row 1 (Company Info)', default=True)
    footer_row1_content = fields.Html(
        string='Row 1 Content',
        default='<p style="margin:0;"><strong>{{company.name}}</strong> | {{company.phone}} | {{company.email}}</p>',
        help='Use {{company.field_name}} for dynamic company data. Example: {{company.name}}, {{company.phone}}, {{company.email}}'
    )
    footer_row1_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right'),
        ('justify', 'Justified'),
        ('split', 'Split (Left/Right columns)')
    ], string='Row 1 Alignment', default='center')
    footer_row1_left_content = fields.Html(string='Row 1 Left Column', help='Only used if alignment is "Split"')
    footer_row1_right_content = fields.Html(string='Row 1 Right Column', help='Only used if alignment is "Split"')

    # Row 2: Contact Information
    footer_row2_enable = fields.Boolean(string='Enable Row 2 (Contact Info)', default=True)
    footer_row2_content = fields.Html(
        string='Row 2 Content',
        default='<p style="margin:0;">{{company.street}}, {{company.city}}, {{company.state_id.name}} {{company.zip}} | Website: {{company.website}}</p>',
        help='Use {{company.field_name}} for dynamic company data'
    )
    footer_row2_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right'),
        ('justify', 'Justified'),
        ('split', 'Split (Left/Right columns)')
    ], string='Row 2 Alignment', default='center')
    footer_row2_left_content = fields.Html(string='Row 2 Left Column')
    footer_row2_right_content = fields.Html(string='Row 2 Right Column')

    # Row 3: Bank Information
    footer_row3_enable = fields.Boolean(string='Enable Row 3 (Bank Info)', default=True)
    footer_row3_content = fields.Html(
        string='Row 3 Content',
        default='<p style="margin:0; font-size:0.85em;"><em>Bank: {{company.partner_id.bank_ids[0].bank_id.name}} | Account: {{company.partner_id.bank_ids[0].acc_number}} | SWIFT: {{company.partner_id.bank_ids[0].bank_id.bic}}</em></p>',
        help='Use {{company.partner_id.bank_ids[0].field_name}} for bank data'
    )
    footer_row3_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right'),
        ('justify', 'Justified'),
        ('split', 'Split (Left/Right columns)')
    ], string='Row 3 Alignment', default='center')
    footer_row3_left_content = fields.Html(string='Row 3 Left Column')
    footer_row3_right_content = fields.Html(string='Row 3 Right Column')

    # Footer Standard Content (when not using custom sections)
    footer_show_bank_details = fields.Boolean(string='Show Bank Details (Standard)', default=True)
    footer_show_page_numbers = fields.Boolean(string='Show Page Numbers', default=True)
    footer_show_document_name = fields.Boolean(string='Show Document Name', default=True)

    # Footer Alignment (Standard mode)
    footer_bank_details_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right')
    ], string='Bank Details Alignment', default='center')
    footer_page_numbers_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right')
    ], string='Page Numbers Alignment', default='center')

    # ========== SPACING & MARGINS ==========
    header_padding_top = fields.Integer(string='Header Top Padding (px)', default=20)
    header_padding_bottom = fields.Integer(string='Header Bottom Padding (px)', default=10)
    footer_padding_top = fields.Integer(string='Footer Top Padding (px)', default=16)
    footer_padding_bottom = fields.Integer(string='Footer Bottom Padding (px)', default=10)
    body_margin_top = fields.Integer(string='Body Top Margin (px)', default=0)
    body_margin_bottom = fields.Integer(string='Body Bottom Margin (px)', default=0)

    # Row Spacing
    footer_row_spacing = fields.Integer(string='Space Between Footer Rows (px)', default=8)

    # ========== COLORS ==========
    primary_accent_color = fields.Char(string='Primary Accent Color', default='#875a7b', help='Override company primary color')
    secondary_accent_color = fields.Char(string='Secondary Accent Color', default='#21b799', help='Override company secondary color')
    text_color_header = fields.Char(string='Header Text Color', default='#000000')
    text_color_body = fields.Char(string='Body Text Color', default='#000000')
    text_color_footer = fields.Char(string='Footer Text Color', default='#6c757d')

    @api.model
    def get_config(self, company_id=None):
        """Get configuration for a company, or create default if not exists"""
        if not company_id:
            company_id = self.env.company.id

        # Check if company exists (to avoid creating config for transient/deleted companies)
        company = self.env['res.company'].browse(company_id).exists()
        if not company:
            return self.browse()  # Return empty recordset

        config = self.search([('company_id', '=', company_id)], limit=1)
        if not config:
            config = self.create({
                'company_id': company_id,
                'name': f'VPA Layout Config - {company.name}'
            })
        return config

    def action_load_company_details(self):
        """Load company details into HTML editor so user can edit and style it"""
        self.ensure_one()
        if not self.company_id:
            return

        company = self.company_id

        # Generate HTML from company details
        if company.company_details:
            # Company has custom company_details - use it (handle translatable field)
            if isinstance(company.company_details, dict):
                # Get current user's language or default to en_US
                lang = self.env.user.lang or 'en_US'
                html_content = company.company_details.get(lang) or company.company_details.get('en_US', '')
            else:
                html_content = company.company_details
        else:
            # Generate from partner address
            partner = company.partner_id
            html_parts = []

            if partner.name:
                html_parts.append(f'<strong>{partner.name}</strong>')

            if partner.street:
                html_parts.append(partner.street)

            if partner.street2:
                html_parts.append(partner.street2)

            city_state_zip = []
            if partner.city:
                city_state_zip.append(partner.city)
            if partner.state_id:
                city_state_zip.append(partner.state_id.name)
            if partner.zip:
                city_state_zip.append(partner.zip)
            if city_state_zip:
                html_parts.append(' '.join(city_state_zip))

            if partner.country_id:
                html_parts.append(partner.country_id.name)

            if partner.phone:
                html_parts.append(f'Phone: {partner.phone}')

            if partner.email:
                html_parts.append(f'Email: {partner.email}')

            html_content = '<br/>'.join(html_parts) if html_parts else ''

        # Update the field with better line spacing
        if html_content:
            # Wrap in div with controlled line height instead of <p> which has default margins
            self.header_company_details_html = f'<div style="line-height: 1.4;">{html_content}</div>'
        else:
            self.header_company_details_html = '<div>No company details found</div>'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Company Details Loaded',
                'message': 'You can now edit and style the company details in the HTML editor below. Adjust line-height in the div style to control spacing.',
                'type': 'success',
                'sticky': False,
            }
        }

    @api.depends('header_logo_position', 'header_company_details_position', 'header_company_details_html',
                 'header_logo_width', 'header_logo_height',
                 'header_show_tagline', 'header_tagline_position', 'header_show_circle', 'header_circle_size',
                 'header_circle_opacity', 'header_circle_color', 'header_show_vat',
                 'footer_row1_content', 'footer_row2_content', 'footer_row3_content',
                 'footer_row1_enable', 'footer_row2_enable', 'footer_row3_enable',
                 'footer_enable_custom_sections', 'footer_layout',
                 'body_table_style', 'body_title_position', 'body_title_size',
                 'primary_accent_color', 'secondary_accent_color',
                 'text_color_header', 'text_color_body', 'text_color_footer')
    def _compute_preview(self):
        """Generate live preview of the document layout - Following Odoo's base.document.layout pattern"""
        styles = self._get_asset_style()

        for config in self:
            if config.company_id:
                try:
                    # Ensure bin_size is False to get actual binary data for logo
                    if config.env.context.get('bin_size'):
                        config = config.with_context(bin_size=False)

                    # Use the same approach as base.document.layout
                    config.preview = self.env['ir.ui.view']._render_template(
                        'vpa_document_layout.vpa_preview_with_container',
                        config._get_render_information(styles)
                    )
                except Exception as e:
                    # If preview fails, show detailed error
                    import traceback
                    error_detail = traceback.format_exc()
                    config.preview = f'''<!DOCTYPE html>
<html>
<body style="padding: 20px; font-family: Arial, sans-serif;">
    <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px;">
        <h4>Preview Unavailable</h4>
        <p><strong>Error:</strong> {str(e)}</p>
        <details>
            <summary>Technical Details</summary>
            <pre style="font-size: 11px; overflow: auto;">{error_detail}</pre>
        </details>
    </div>
</body>
</html>'''
            else:
                config.preview = '''<!DOCTYPE html>
<html>
<body style="padding: 20px; font-family: Arial, sans-serif;">
    <div style="background: #d1ecf1; border: 1px solid #0c5460; padding: 15px; border-radius: 5px;">
        <p>Please select a company to see preview.</p>
    </div>
</body>
</html>'''

    def _get_asset_style(self):
        """Compile the style template for preview - Following Odoo's base.document.layout pattern"""
        company_styles = self.env['ir.qweb']._render('vpa_document_layout.styles_vpa_report', {
            'company_ids': self,
        }, raise_if_not_found=False)
        return company_styles

    @api.model
    def _get_css_for_preview(self, scss, new_id):
        """Compile SCSS into CSS - Following Odoo's base.document.layout pattern"""
        if not scss or not scss.strip():
            return ""
        from markupsafe import Markup
        from odoo.addons.base.models.assetsbundle import ScssStylesheetAsset
        asset = ScssStylesheetAsset(None, inline='// css_for_preview')
        css_code = asset.compile(scss)
        return Markup(css_code) if isinstance(scss, Markup) else css_code

    def _get_render_information(self, styles):
        """Get rendering context - Following Odoo's base.document.layout pattern"""
        self.ensure_one()
        preview_css = self._get_css_for_preview(styles, self.id)

        # Import image_data_uri helper function from correct location
        from odoo.tools.image import image_data_uri

        return {
            'config': self,
            'company': self.company_id,  # Company already loaded with bin_size=False from _compute_preview
            'preview_css': preview_css,
            'image_data_uri': image_data_uri,  # Add helper function to context
        }
