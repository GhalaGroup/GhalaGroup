# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class VPADocumentTemplate(models.Model):
    _name = 'vpa.document.template'
    _description = 'VPA Document Template'
    _order = 'sequence, name'

    # Basic Information
    name = fields.Char(string='Template Name', required=True, help='Name shown in print menu (e.g., "Modern Sales Quote")')
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', default=10, help='Order in print menu')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    # Logo - related field like base.document.layout
    logo = fields.Binary(related='company_id.logo', readonly=True, string="Company Logo")
    partner_id = fields.Many2one(related='company_id.partner_id', readonly=True, string="Company Partner")
    company_details = fields.Html(related='company_id.company_details', readonly=True, string="Company Details")

    # Target Configuration
    target_app = fields.Selection([
        ('sale', 'Sales'),
        ('account', 'Invoicing'),
        ('purchase', 'Purchase'),
        ('stock', 'Inventory'),
        ('mrp', 'Manufacturing'),
    ], string='Target App', required=True, help='Which Odoo app this template is for')

    document_type = fields.Selection([
        ('quotation', 'Quotation'),
        ('sale_order', 'Sales Order'),
        ('invoice', 'Invoice'),
        ('bill', 'Vendor Bill'),
        ('purchase_order', 'Purchase Order'),
        ('delivery', 'Delivery Order'),
        ('picking', 'Picking'),
        ('manufacturing_order', 'Manufacturing Order'),
    ], string='Document Type', required=True, help='Which document type this template applies to')

    # Odoo Header/Footer Control
    hide_odoo_header = fields.Boolean(string='Hide Standard Odoo Header', default=True)
    hide_odoo_footer = fields.Boolean(string='Hide Standard Odoo Footer', default=True)

    # Header Settings
    header_logo_alignment = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right'),
    ], string='Logo Alignment', default='right')
    header_logo_width = fields.Integer(string='Logo Width (px)', default=250)
    header_logo_height = fields.Integer(string='Logo Height (px)', default=100)
    header_logo_aspect_ratio = fields.Selection([
        ('auto', 'Auto (Maintain Aspect Ratio)'),
        ('fixed', 'Fixed (Force Width & Height)'),
    ], string='Logo Sizing', default='auto', help='Auto maintains aspect ratio, Fixed forces exact dimensions')
    header_show_circle = fields.Boolean(string='Show Decorative Circle', default=True)
    header_circle_size = fields.Integer(string='Circle Size (px)', default=300)
    header_circle_opacity = fields.Float(string='Circle Opacity', default=0.25, help='0.0 to 1.0')

    # Company Information Settings
    header_company_info_alignment = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right'),
    ], string='Company Info Alignment', default='right')
    header_company_details_html = fields.Html(string='Company Details (Custom HTML)', help='Leave empty to use company address')
    header_company_info_color = fields.Char(string='Company Info Font Color', default='#555555', help='Color for company information text')

    # Colors
    primary_accent_color = fields.Char(string='Primary Color', default='#875a7b', help='Used for headers, titles')
    secondary_accent_color = fields.Char(string='Secondary Color', default='#21b799', help='Used for accents, borders')

    # Table Settings
    table_style = fields.Selection([
        ('modern_light', 'Modern Light - Clean with subtle colors'),
        ('modern_gradient', 'Modern Gradient - Elegant gradient header'),
        ('bold_primary', 'Bold Primary - Strong colored header'),
        ('minimal_lines', 'Minimal Lines - Simple borders only'),
        ('striped_elegant', 'Striped Elegant - Alternating row colors'),
        ('corporate_blue', 'Corporate Blue - Professional blue theme'),
        ('fresh_green', 'Fresh Green - Clean green accents'),
        ('premium_purple', 'Premium Purple - Luxurious purple tones'),
    ], string='Table Style', default='modern_light', help='Choose table design style')
    table_header_bg_color = fields.Char(string='Table Header Background', default='#f5f5f5')
    table_header_text_color = fields.Char(string='Table Header Text', default='#333333')
    table_border_color = fields.Char(string='Table Border Color', default='#e0e0e0')
    table_row_alt_bg = fields.Char(string='Alternate Row Background', default='#fafafa')

    # Paper Settings
    paper_size = fields.Selection([
        ('a4', 'A4 (210mm x 297mm)'),
        ('letter', 'Letter (8.5in x 11in)'),
    ], string='Paper Size', default='a4', required=True)
    paper_orientation = fields.Selection([
        ('portrait', 'Portrait'),
        ('landscape', 'Landscape'),
    ], string='Orientation', default='portrait', required=True)

    # Footer Settings
    footer_show_shape = fields.Boolean(string='Show Footer Wave Shape', default=True)
    footer_shape_opacity = fields.Float(string='Footer Shape Opacity', default=0.1)
    footer_layout = fields.Selection([
        ('single', 'Single Column'),
        ('two_col', 'Two Columns'),
        ('three_col', 'Three Columns'),
    ], string='Footer Layout', default='two_col', help='Number of columns in footer')
    footer_bank_details_show = fields.Boolean(string='Show Bank Details', default=True)
    footer_column_1_title = fields.Char(string='Column 1 Title', default='Payment Terms')
    footer_column_1_content = fields.Html(string='Column 1 Content', default='<p>30 Days</p>')
    footer_column_2_title = fields.Char(string='Column 2 Title', default='Bank Details')
    footer_column_2_content = fields.Html(string='Column 2 Content')
    footer_column_3_title = fields.Char(string='Column 3 Title', default='Contact Info')
    footer_column_3_content = fields.Html(string='Column 3 Content')
    footer_custom_html = fields.Html(string='Custom Footer HTML')

    # Report Action Reference (auto-created)
    report_action_id = fields.Many2one('ir.actions.report', string='Report Action', readonly=True, ondelete='cascade')

    # Preview field (like the old VPA config)
    preview = fields.Html(compute='_compute_preview', sanitize=False)

    @api.depends('name', 'primary_accent_color', 'secondary_accent_color',
                 'header_logo_alignment', 'header_logo_width', 'header_logo_height', 'header_logo_aspect_ratio',
                 'header_company_info_alignment', 'header_company_details_html', 'header_company_info_color',
                 'header_show_circle', 'header_circle_size', 'header_circle_opacity',
                 'table_style', 'table_header_bg_color', 'table_header_text_color', 'table_border_color', 'table_row_alt_bg',
                 'footer_show_shape', 'footer_shape_opacity', 'footer_layout', 'footer_bank_details_show',
                 'footer_column_1_title', 'footer_column_1_content',
                 'footer_column_2_title', 'footer_column_2_content',
                 'footer_column_3_title', 'footer_column_3_content',
                 'paper_size', 'paper_orientation')
    def _compute_preview(self):
        """Generate live preview - following Odoo's base.document.layout pattern"""
        for template in self:
            if template.id and template.company_id:
                try:
                    # Ensure bin_size is False to load actual binary data (like base.document.layout does)
                    if template.env.context.get('bin_size'):
                        template = template.with_context(bin_size=False)

                    # Render preview directly like the old config does
                    import logging
                    import re
                    _logger = logging.getLogger(__name__)
                    _logger.info(f"Computing preview for template {template.id}, company {template.company_id.name}")
                    preview_html = self.env['ir.ui.view']._render_template(
                        'vpa_document_layout.vpa_template_preview_container',
                        template._get_preview_context()
                    )

                    # Remove any body { width: ... } styles that would affect the parent page
                    # These styles are for PDF generation, not for the live preview
                    preview_html = re.sub(r'(html|body)\s*{[^}]*width[^}]*}', lambda m: m.group(0).replace('width:', 'x-width:'), preview_html, flags=re.IGNORECASE)
                    template.preview = preview_html
                except Exception as e:
                    import traceback
                    import logging
                    _logger = logging.getLogger(__name__)
                    error_detail = traceback.format_exc()
                    _logger.error(f"Preview error for template {template.id}: {error_detail}")
                    template.preview = f'''<div style="padding: 20px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 5px;">
                        <h4>Preview Unavailable</h4>
                        <p><strong>Error:</strong> {str(e)}</p>
                        <details><summary>Details</summary><pre>{error_detail}</pre></details>
                    </div>'''
            else:
                template.preview = '''
                <div style="text-align: center; padding: 100px 20px; color: #999;">
                    <i class="fa fa-file-pdf-o fa-4x" style="margin-bottom: 20px; opacity: 0.3;"></i>
                    <p style="font-size: 14pt;">Save the template to see live preview</p>
                </div>
                '''

    def _get_preview_context(self):
        """Get context for preview rendering - following base.document.layout pattern"""
        self.ensure_one()
        from odoo.tools.image import image_data_uri

        # Like base.document.layout, pass self (which has logo field) as company
        # Ensure bin_size is False to load actual binary data
        if self.env.context.get('bin_size'):
            template_with_logo = self.with_context(bin_size=False)
        else:
            template_with_logo = self

        return {
            'template': template_with_logo,
            'company': template_with_logo,  # Pass template itself (has logo field)
            'vpa_template': template_with_logo,
            'image_data_uri': image_data_uri,
        }

    @api.model
    def create(self, vals):
        """Create template and generate corresponding report action"""
        template = super(VPADocumentTemplate, self).create(vals)
        template._create_report_action()
        return template

    def write(self, vals):
        """Update template and refresh report action"""
        result = super(VPADocumentTemplate, self).write(vals)

        # Fields that require template regeneration
        template_fields = [
            'header_logo_alignment', 'header_logo_width', 'header_logo_height',
            'header_logo_aspect_ratio', 'header_company_info_alignment', 'header_company_details_html',
            'header_show_circle', 'header_circle_size', 'header_circle_opacity',
            'primary_accent_color', 'secondary_accent_color',
            'footer_show_shape', 'footer_shape_opacity', 'footer_bank_details_show'
        ]

        # Check if any template field was updated
        if any(field in vals for field in template_fields):
            for template in self:
                # Delete old views
                existing_views = self.env['ir.ui.view'].search([
                    '|', '|',
                    ('key', 'like', f'%template_{template.id}%'),
                    ('key', 'like', f'%inherit_{template.id}%'),
                    ('name', 'like', f'%{template.id}')
                ])
                existing_views.unlink()

                # Regenerate
                template._create_qweb_template()

        # Update report action name if name changed
        for template in self:
            if template.report_action_id:
                template._update_report_action()

        return result

    def unlink(self):
        """Delete template and its report action"""
        for template in self:
            if template.report_action_id:
                template.report_action_id.unlink()
        return super(VPADocumentTemplate, self).unlink()

    def _create_report_action(self):
        """Create a new report action for this template"""
        self.ensure_one()

        # Determine model based on document type
        model_map = {
            'quotation': 'sale.order',
            'sale_order': 'sale.order',
            'invoice': 'account.move',
            'bill': 'account.move',
            'purchase_order': 'purchase.order',
            'delivery': 'stock.picking',
            'picking': 'stock.picking',
            'manufacturing_order': 'mrp.production',
        }

        model = model_map.get(self.document_type, 'sale.order')

        # Get or create A4 paperformat
        paperformat = self.env['report.paperformat'].search([
            ('name', '=', 'VPA A4'),
            ('format', '=', 'A4'),
        ], limit=1)

        if not paperformat:
            paperformat = self.env['report.paperformat'].create({
                'name': 'VPA A4',
                'format': 'A4',
                'orientation': 'Portrait',
                'margin_top': 0,
                'margin_bottom': 0,
                'margin_left': 0,
                'margin_right': 0,
                'header_spacing': 0,
                'dpi': 96,
            })

        # Build print report name expression
        # Format: Quote Number - Client Name (Customer Reference)
        # Example: S00001 - Deco Addict (EA123) or S00001 - Deco Addict (if no ref)
        print_name_expr = "(object.name or 'Document') + ' - ' + (object.partner_id.name or 'Customer') + (((' (' + object.client_order_ref + ')') if object.client_order_ref else ''))"

        # Create report action
        report_action = self.env['ir.actions.report'].create({
            'name': self.name,
            'model': model,
            'report_type': 'qweb-pdf',
            'report_name': f'vpa_document_layout.report_template_{self.id}',
            'report_file': f'vpa_document_layout.report_template_{self.id}',
            'print_report_name': print_name_expr,
            'binding_model_id': self.env['ir.model']._get(model).id,
            'binding_type': 'report',
            'paperformat_id': paperformat.id,
        })

        self.report_action_id = report_action.id

        # Create the QWeb template
        self._create_qweb_template()

    def _update_report_action(self):
        """Update existing report action"""
        self.ensure_one()
        if self.report_action_id:
            self.report_action_id.write({
                'name': self.name,
            })

    def action_load_company_details(self):
        """Load company details into the HTML field"""
        self.ensure_one()

        company = self.company_id
        html_parts = []

        if company.name:
            html_parts.append(f'<strong style="font-size: 11pt;">{company.name}</strong>')

        if company.street:
            html_parts.append(company.street)
        if company.street2:
            html_parts.append(company.street2)

        city_parts = []
        if company.city:
            city_parts.append(company.city)
        if company.zip:
            city_parts.append(company.zip)
        if city_parts:
            html_parts.append(' '.join(city_parts))

        if company.state_id:
            html_parts.append(company.state_id.name)
        if company.country_id:
            html_parts.append(company.country_id.name)

        if company.phone:
            html_parts.append(f'Phone: {company.phone}')
        if company.email:
            html_parts.append(f'Email: {company.email}')
        if company.website:
            html_parts.append(f'Web: {company.website}')

        self.header_company_details_html = '<br/>'.join(html_parts)

        # Return action to reload the form
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.document.template',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _get_table_styles(self):
        """Generate CSS for table based on selected style"""
        self.ensure_one()

        style_presets = {
            'modern_light': {
                'header_bg': '#f8f9fa',
                'header_text': '#2c3e50',
                'border': '#dee2e6',
                'alt_row': '#f8f9fa',
                'header_border_bottom': '3px solid #3498db',
            },
            'modern_gradient': {
                'header_bg': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'header_text': '#ffffff',
                'border': '#e0e0e0',
                'alt_row': '#f9f9f9',
                'header_border_bottom': 'none',
            },
            'bold_primary': {
                'header_bg': self.primary_accent_color,
                'header_text': '#ffffff',
                'border': self.primary_accent_color,
                'alt_row': f'{self.primary_accent_color}15',
                'header_border_bottom': 'none',
            },
            'minimal_lines': {
                'header_bg': '#ffffff',
                'header_text': '#2c3e50',
                'border': '#e0e0e0',
                'alt_row': 'transparent',
                'header_border_bottom': '2px solid #2c3e50',
            },
            'striped_elegant': {
                'header_bg': '#34495e',
                'header_text': '#ecf0f1',
                'border': '#bdc3c7',
                'alt_row': '#ecf0f1',
                'header_border_bottom': 'none',
            },
            'corporate_blue': {
                'header_bg': 'linear-gradient(to right, #2c3e50, #3498db)',
                'header_text': '#ffffff',
                'border': '#3498db',
                'alt_row': '#ebf5fb',
                'header_border_bottom': 'none',
            },
            'fresh_green': {
                'header_bg': '#27ae60',
                'header_text': '#ffffff',
                'border': '#27ae60',
                'alt_row': '#e8f8f5',
                'header_border_bottom': 'none',
            },
            'premium_purple': {
                'header_bg': 'linear-gradient(135deg, #9b59b6, #8e44ad)',
                'header_text': '#ffffff',
                'border': '#9b59b6',
                'alt_row': '#f4ecf7',
                'header_border_bottom': 'none',
            },
        }

        preset = style_presets.get(self.table_style, style_presets['modern_light'])

        # Use custom colors if provided, otherwise use preset
        return {
            'header_bg': self.table_header_bg_color if self.table_header_bg_color != '#f5f5f5' else preset['header_bg'],
            'header_text': self.table_header_text_color if self.table_header_text_color != '#333333' else preset['header_text'],
            'border': self.table_border_color if self.table_border_color != '#e0e0e0' else preset['border'],
            'alt_row': self.table_row_alt_bg if self.table_row_alt_bg != '#fafafa' else preset['alt_row'],
            'header_border_bottom': preset['header_border_bottom'],
        }

    def _get_logo_style(self):
        """Generate CSS style for logo based on aspect ratio setting"""
        self.ensure_one()
        if self.header_logo_aspect_ratio == 'fixed':
            # Force exact width and height
            return f'width: {self.header_logo_width}px; height: {self.header_logo_height}px;'
        else:
            # Maintain aspect ratio with max constraints
            return f'max-width: {self.header_logo_width}px; max-height: {self.header_logo_height}px;'

    def _get_paper_dimensions(self):
        """Get paper dimensions based on size and orientation"""
        self.ensure_one()

        # Define dimensions in mm (portrait)
        dimensions = {
            'a4': {'width': 210, 'height': 297},
            'letter': {'width': 215.9, 'height': 279.4},  # 8.5in x 11in in mm
        }

        dims = dimensions.get(self.paper_size, dimensions['a4'])

        # Swap if landscape
        if self.paper_orientation == 'landscape':
            dims = {'width': dims['height'], 'height': dims['width']}

        return dims

    def _get_page_size_css(self):
        """Get CSS @page size declaration"""
        self.ensure_one()
        size_name = 'A4' if self.paper_size == 'a4' else 'Letter'
        return f'size: {size_name} {self.paper_orientation};'

    def _create_qweb_template(self):
        """Create QWeb template for this document template"""
        self.ensure_one()

        # Determine which document template to call based on document type
        document_template_map = {
            'quotation': 'sale.report_saleorder_document',
            'sale_order': 'sale.report_saleorder_document',
            'invoice': 'account.report_invoice_document',
            'bill': 'account.report_invoice_document',
        }

        doc_template = document_template_map.get(self.document_type, 'sale.report_saleorder_document')

        # Create inheritance view to replace web.external_layout call in document template
        # Get the inherit_id for the document template
        doc_template_view = self.env.ref(doc_template.replace('.', '_').replace('_', '.', 1), raise_if_not_found=False)

        if doc_template_view:
            try:
                inherit_view = self.env['ir.ui.view'].create({
                    'name': f'VPA {doc_template} Inherit {self.id}',
                    'type': 'qweb',
                    'mode': 'extension',
                    'inherit_id': doc_template_view.id,
                    'key': f'vpa_document_layout.{doc_template.replace(".", "_")}_inherit_{self.id}',
                    'arch': f'''<xpath expr="//t[@t-call='web.external_layout']" position="attributes">
    <attribute name="t-call">vpa_document_layout.external_layout_vpa_template_{self.id}</attribute>
</xpath>''',
                })
            except Exception as e:
                # If xpath not found (already replaced by another template), skip inheritance view
                _logger.info(f"Skipping inheritance view for template {self.id}: {str(e)}")

        # Create the main report template
        main_template = self.env['ir.ui.view'].create({
            'name': f'VPA Report Template {self.id}',
            'type': 'qweb',
            'key': f'vpa_document_layout.report_template_{self.id}',
            'arch': f'''<t t-name="vpa_document_layout.report_template_{self.id}">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="doc">
            <t t-call="{doc_template}" t-lang="doc.partner_id.lang"/>
        </t>
    </t>
</t>''',
        })

        # Create the external layout template with custom styling
        # Get paper dimensions
        dims = self._get_paper_dimensions()
        page_width = dims['width']
        page_height = dims['height']
        page_size_css = self._get_page_size_css()

        # Build arch content without f-string to avoid {{{{ escaping issues
        arch_content = '''<t t-name="vpa_document_layout.external_layout_vpa_template_%s">
    <t t-set="vpa_template" t-value="env['vpa.document.template'].browse(%s)"/>
    <t t-set="company" t-value="company or env.company"/>
    <t t-set="primary_color" t-value="'%s'"/>
    <t t-set="secondary_color" t-value="'%s'"/>

    <div t-attf-class="article o_report_layout_vpa o_company_#{company.id}_layout" style="font-family: 'Lato', 'Helvetica', 'Arial', sans-serif;">

        <style type="text/css">
            @page {
                margin: 0mm;
                padding: 0mm;
                %s
            }
            body {
                margin: 0;
                padding: 0;
            }
            .o_report_layout_vpa {
                position: relative;
                width: %smm;
                height: %smm;
                padding: 0;
                box-sizing: border-box;
                overflow: hidden;
            }
            .o_report_layout_vpa .page {
                position: relative;
                z-index: 2;
                width: 100%%;
                height: 100%%;
                padding: 20px;
                padding-bottom: 120px;
                box-sizing: border-box;
            }
            /* Main product table - ensure visibility in PDF */
            table.o_main_table, .o_report_layout_vpa table.o_main_table {
                border-collapse: collapse !important;
                border-spacing: 0 !important;
                width: 100%% !important;
                border: 2px solid %s !important;
                margin-bottom: 20px !important;
            }
            table.o_main_table thead, .o_report_layout_vpa table.o_main_table thead {
                background: %s !important;
                color: %s !important;
                font-weight: bold !important;
                %s
            }
            table.o_main_table thead th, .o_report_layout_vpa table.o_main_table thead th {
                background: %s !important;
                color: %s !important;
                padding: 12px 8px !important;
                font-weight: bold !important;
                border: 1px solid %s !important;
                text-align: left !important;
            }
            table.o_main_table tbody td, .o_report_layout_vpa table.o_main_table tbody td {
                padding: 10px 8px !important;
                border: 1px solid #e0e0e0 !important;
                vertical-align: top !important;
            }
            table.o_main_table tbody tr:nth-child(even), .o_report_layout_vpa table.o_main_table tbody tr:nth-child(even) {
                background-color: %s !important;
            }
            table.o_main_table tbody tr:nth-child(odd), .o_report_layout_vpa table.o_main_table tbody tr:nth-child(odd) {
                background-color: #ffffff !important;
            }
            .vpa_company_info, .vpa_company_info * {
                color: inherit !important;
            }
            /* Totals table styling */
            .o_report_layout_vpa table.o_total_table {
                border-collapse: collapse !important;
                width: 100%% !important;
                margin-top: 20px !important;
            }
            .o_report_layout_vpa table.o_total_table td {
                padding: 8px 12px !important;
                border: none !important;
                font-size: 10pt !important;
            }
            .o_report_layout_vpa table.o_total_table tr {
                border-bottom: 1px solid #e0e0e0 !important;
            }
            .o_report_layout_vpa table.o_total_table tr:last-child {
                border-top: 2px solid #000 !important;
                font-weight: bold !important;
                font-size: 11pt !important;
            }
            .o_report_layout_vpa .o_price_total {
                font-weight: bold !important;
                font-size: 12pt !important;
            }
        </style>

        <!-- Page Content Wrapper -->
        <div class="page">
            <!-- Decorative circle -->
            <svg t-if="%s" style="position: absolute; top: -100px; right: -100px; z-index: 0;" width="%s" height="%s" xmlns="http://www.w3.org/2000/svg">
                <circle cx="%s" cy="%s" r="%s" fill="%s" fill-opacity="%s"/>
            </svg>

            <!-- Footer Wave Shape - positioned at bottom, extends beyond boundaries like circle -->
            <svg t-if="%s" style="position: absolute; bottom: -100px; left: -50px; width: 120%%; height: 300px; z-index: 0;" viewBox="0 0 1200 120" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M0,120 L0,30 C150,60 350,0 600,30 C850,60 1050,0 1200,30 L1200,120 Z" t-attf-fill="%s" t-att-fill-opacity="%s"/>
            </svg>

            <!-- Header -->
        <div t-attf-style="position: relative; z-index: 1; padding-bottom: 15px; margin-bottom: 25px; border-bottom: 4px solid %s;">
            <div style="text-align: %s; margin-bottom: 10px;">
                <!-- Use image_data_uri for both preview and PDF - company must have bin_size=False -->
                <img t-if="company.logo" t-att-src="image_data_uri(company.logo)" style="%s" alt="Logo"/>
            </div>
            <div class="vpa_company_info" t-attf-style="text-align: %s; font-size: 9pt; line-height: 1.5; color: %s !important;">
                <t t-if="vpa_template.header_company_details_html">
                    <span t-attf-style="color: %s !important;"><t t-out="vpa_template.header_company_details_html"/></span>
                </t>
                <t t-elif="company.company_details">
                    <span t-attf-style="color: %s !important;" t-field="company.company_details"/>
                </t>
                <t t-else="">
                    <span t-attf-style="color: %s !important;" t-field="company.partner_id" t-options='{"widget": "contact", "fields": ["address", "name"], "no_marker": true}'/>
                </t>
            </div>
        </div>

        <!-- Customer Address and Document Info (Two columns like standard Odoo) -->
        <table t-if="address or information_block" style="width: 100%%; margin-bottom: 25px; border-collapse: collapse;">
            <tbody>
                <tr>
                    <td t-if="address" style="width: 50%%; vertical-align: top; padding-right: 20px;">
                        <t t-out="address"/>
                    </td>
                    <td t-if="information_block" style="width: 50%%; vertical-align: bottom; text-align: right; padding-left: 20px;">
                        <h2 t-if="layout_document_title" t-attf-style="font-size: 28pt; font-weight: bold; color: %s; margin: 0; text-align: right;" t-out="layout_document_title"/>
                        <div style="margin-top: 15px; font-size: 9pt; line-height: 1.8; color: #555; text-align: right;">
                            <t t-out="information_block"/>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>

            <!-- Document content -->
            <t t-out="0"/>

            <!-- Footer - absolute position at bottom -->
            <div style="position: absolute; bottom: 0; left: 0; right: 0; z-index: 100; min-height: 100px;">
            <!-- Footer Content with Columns -->
            <div style="position: relative; z-index: 1; padding: 40px 20px 15px 20px; font-size: 7pt;">
                <!-- Single Column Layout -->
                <div t-if="vpa_template.footer_layout == 'single'" style="text-align: center;">
                    <div t-if="vpa_template.footer_column_1_title or vpa_template.footer_column_1_content">
                        <strong t-if="vpa_template.footer_column_1_title" style="display: block; margin-bottom: 4px; font-size: 8pt; color: %s;" t-out="vpa_template.footer_column_1_title"/>
                        <div t-if="vpa_template.footer_column_1_content" style="color: #666; line-height: 1.6;">
                            <t t-out="vpa_template.footer_column_1_content"/>
                        </div>
                    </div>
                    <!-- Bank Details for single column -->
                    <div t-if="%s and company.partner_id.bank_ids" style="margin-top: 8px; color: #666;">
                        <strong style="display: block; margin-bottom: 3px; font-size: 8pt;">Bank Details:</strong>
                        <t t-foreach="company.partner_id.bank_ids[:1]" t-as="bank">
                            <span t-field="bank.bank_id.name"/> - <span t-field="bank.acc_number"/>
                        </t>
                    </div>
                </div>

                <!-- Two Column Layout -->
                <table t-if="vpa_template.footer_layout == 'two_col'" style="width: 100%%; border-collapse: collapse;">
                    <tr>
                        <td style="width: 50%%; vertical-align: top; padding-right: 15px;">
                            <div t-if="vpa_template.footer_column_1_title or vpa_template.footer_column_1_content">
                                <strong t-if="vpa_template.footer_column_1_title" style="display: block; margin-bottom: 4px; font-size: 8pt; color: %s;" t-out="vpa_template.footer_column_1_title"/>
                                <div t-if="vpa_template.footer_column_1_content" style="color: #666; line-height: 1.6;">
                                    <t t-out="vpa_template.footer_column_1_content"/>
                                </div>
                            </div>
                        </td>
                        <td style="width: 50%%; vertical-align: top; padding-left: 15px;">
                            <div t-if="vpa_template.footer_column_2_title or vpa_template.footer_column_2_content">
                                <strong t-if="vpa_template.footer_column_2_title" style="display: block; margin-bottom: 4px; font-size: 8pt; color: %s;" t-out="vpa_template.footer_column_2_title"/>
                                <div t-if="vpa_template.footer_column_2_content" style="color: #666; line-height: 1.6;">
                                    <t t-out="vpa_template.footer_column_2_content"/>
                                </div>
                                <!-- Bank Details for two columns (right side) -->
                                <div t-if="%s and company.partner_id.bank_ids and not vpa_template.footer_column_2_content" style="color: #666;">
                                    <t t-foreach="company.partner_id.bank_ids[:1]" t-as="bank">
                                        <span t-field="bank.bank_id.name"/><br/>
                                        <span t-field="bank.acc_number"/>
                                    </t>
                                </div>
                            </div>
                        </td>
                    </tr>
                </table>

                <!-- Three Column Layout -->
                <table t-if="vpa_template.footer_layout == 'three_col'" style="width: 100%%; border-collapse: collapse;">
                    <tr>
                        <td style="width: 33.33%%; vertical-align: top; padding-right: 10px;">
                            <div t-if="vpa_template.footer_column_1_title or vpa_template.footer_column_1_content">
                                <strong t-if="vpa_template.footer_column_1_title" style="display: block; margin-bottom: 4px; font-size: 8pt; color: %s;" t-out="vpa_template.footer_column_1_title"/>
                                <div t-if="vpa_template.footer_column_1_content" style="color: #666; line-height: 1.4; font-size: 7pt;">
                                    <t t-out="vpa_template.footer_column_1_content"/>
                                </div>
                            </div>
                        </td>
                        <td style="width: 33.33%%; vertical-align: top; padding: 0 10px;">
                            <div t-if="vpa_template.footer_column_2_title or vpa_template.footer_column_2_content">
                                <strong t-if="vpa_template.footer_column_2_title" style="display: block; margin-bottom: 4px; font-size: 8pt; color: %s;" t-out="vpa_template.footer_column_2_title"/>
                                <div t-if="vpa_template.footer_column_2_content" style="color: #666; line-height: 1.4; font-size: 7pt;">
                                    <t t-out="vpa_template.footer_column_2_content"/>
                                </div>
                                <!-- Bank Details for three columns (middle) -->
                                <div t-if="%s and company.partner_id.bank_ids and not vpa_template.footer_column_2_content" style="color: #666; font-size: 7.5pt;">
                                    <t t-foreach="company.partner_id.bank_ids[:1]" t-as="bank">
                                        <span t-field="bank.bank_id.name"/><br/>
                                        <span t-field="bank.acc_number"/>
                                    </t>
                                </div>
                            </div>
                        </td>
                        <td style="width: 33.33%%; vertical-align: top; padding-left: 10px;">
                            <div t-if="vpa_template.footer_column_3_title or vpa_template.footer_column_3_content">
                                <strong t-if="vpa_template.footer_column_3_title" style="display: block; margin-bottom: 4px; font-size: 8pt; color: %s;" t-out="vpa_template.footer_column_3_title"/>
                                <div t-if="vpa_template.footer_column_3_content" style="color: #666; line-height: 1.4; font-size: 7pt;">
                                    <t t-out="vpa_template.footer_column_3_content"/>
                                </div>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>
            </div>
        </div>
    </div>
</t>'''

        # Get table styles
        table_styles = self._get_table_styles()

        # Finalize arch_content with all parameters
        arch_content = arch_content % (
            self.id,
            self.id,
            self.primary_accent_color,
            self.secondary_accent_color,
            page_size_css,  # @page size
            page_width,  # Container width
            page_height,  # Container height
            table_styles['border'],  # Table border color
            table_styles['header_bg'],  # Table header background (thead)
            table_styles['header_text'],  # Table header text color (thead)
            table_styles['header_border_bottom'] if table_styles['header_border_bottom'] != 'none' else '',  # Header border bottom
            table_styles['header_bg'],  # Table header background (th)
            table_styles['header_text'],  # Table header text color (th)
            table_styles['border'],  # Table header th border color
            table_styles['alt_row'],  # Alternate row background
            str(self.header_show_circle).lower(),  # Decorative circle
            self.header_circle_size,
            self.header_circle_size,
            self.header_circle_size / 2,
            self.header_circle_size / 2,
            self.header_circle_size / 2,
            self.primary_accent_color,
            self.header_circle_opacity,
            str(self.footer_show_shape).lower(),  # Footer wave shape
            self.secondary_accent_color,  # Footer wave color
            self.footer_shape_opacity,  # Footer wave opacity
            self.primary_accent_color,  # Header border bottom
            self.header_logo_alignment,
            self._get_logo_style(),
            self.header_company_info_alignment,
            self.header_company_info_color,  # Company info div color
            self.header_company_info_color,  # Company info span color (custom HTML)
            self.header_company_info_color,  # Company info span color (company_details)
            self.header_company_info_color,  # Company info span color (partner_id)
            self.primary_accent_color,  # Document title color
            self.primary_accent_color,  # Footer column 1 title color (single)
            str(self.footer_bank_details_show).lower(),  # Bank details (single)
            self.primary_accent_color,  # Footer column 1 title color (two_col)
            self.primary_accent_color,  # Footer column 2 title color (two_col)
            str(self.footer_bank_details_show).lower(),  # Bank details (two_col)
            self.primary_accent_color,  # Footer column 1 title color (three_col)
            self.primary_accent_color,  # Footer column 2 title color (three_col)
            str(self.footer_bank_details_show).lower(),  # Bank details (three_col)
            self.primary_accent_color,  # Footer column 3 title color (three_col)
        )

        layout_template = self.env['ir.ui.view'].create({
            'name': f'VPA External Layout {self.id}',
            'type': 'qweb',
            'key': f'vpa_document_layout.external_layout_vpa_template_{self.id}',
            'arch': arch_content,
        })

    def _get_sample_document(self):
        """Get a sample document for preview based on document type"""
        self.ensure_one()

        model_map = {
            'quotation': 'sale.order',
            'sale_order': 'sale.order',
            'invoice': 'account.move',
            'bill': 'account.move',
            'purchase_order': 'purchase.order',
            'delivery': 'stock.picking',
            'picking': 'stock.picking',
            'manufacturing_order': 'mrp.production',
        }

        model = model_map.get(self.document_type)
        if not model:
            return False

        # Get the first available document of this type
        sample = self.env[model].search([('company_id', '=', self.company_id.id)], limit=1)
        return sample

    def action_regenerate_templates(self):
        """Button action to regenerate QWeb templates"""
        for template in self:
            # Delete existing views (including inheritance views)
            existing_views = self.env['ir.ui.view'].search([
                '|', '|',
                ('key', 'like', f'%template_{template.id}%'),
                ('key', 'like', f'%inherit_{template.id}%'),
                ('name', 'like', f'%{template.id}')
            ])
            existing_views.unlink()

            # Recreate
            template._create_qweb_template()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Templates regenerated successfully!'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_preview_template(self):
        """Open preview of this template"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/vpa/template/preview/{self.id}',
            'target': 'new',
        }
