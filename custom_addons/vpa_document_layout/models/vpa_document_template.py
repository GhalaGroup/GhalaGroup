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

    # PDF Filename Configuration
    print_name_pattern = fields.Selection([
        ('doc_name', 'Document Number Only (e.g., S00001)'),
        ('doc_customer', 'Document Number - Customer Name (e.g., S00001 - Deco Addict)'),
        ('doc_customer_ref', 'Document Number - Customer Name (Ref) (e.g., S00001 - Deco Addict (REF123))'),
        ('doc_customer_ref_date', 'Document Number - Customer Name (Ref) - Date (e.g., S00001 - Deco Addict (REF123) - 2025-01-15)'),
        ('customer_doc', 'Customer Name - Document Number (e.g., Deco Addict - S00001)'),
        ('doc_date', 'Document Number - Date (e.g., S00001 - 2025-01-15)'),
        ('custom', 'Custom Expression'),
    ], string='PDF Filename Pattern', default='doc_customer_ref', required=True,
       help='Choose how the PDF filename will appear when downloaded')

    print_name_expression = fields.Char(
        string='Custom Filename Expression',
        help='Python expression for PDF filename. Available: object (document record). Example: object.name + " - " + object.partner_id.name'
    )

    @api.depends('print_name_pattern', 'print_name_expression')
    def _compute_print_name_preview(self):
        """Show preview of what the filename will look like"""
        for record in self:
            if record.print_name_pattern == 'doc_name':
                record.print_name_preview = 'S00001.pdf'
            elif record.print_name_pattern == 'doc_customer':
                record.print_name_preview = 'S00001 - Deco Addict.pdf'
            elif record.print_name_pattern == 'doc_customer_ref':
                record.print_name_preview = 'S00001 - Deco Addict (REF123).pdf'
            elif record.print_name_pattern == 'doc_customer_ref_date':
                record.print_name_preview = 'S00001 - Deco Addict (REF123) - 2025-01-15.pdf'
            elif record.print_name_pattern == 'customer_doc':
                record.print_name_preview = 'Deco Addict - S00001.pdf'
            elif record.print_name_pattern == 'doc_date':
                record.print_name_preview = 'S00001 - 2025-01-15.pdf'
            elif record.print_name_pattern == 'custom':
                record.print_name_preview = 'Custom expression...'
            else:
                record.print_name_preview = ''

    print_name_preview = fields.Char(string='Preview', compute='_compute_print_name_preview', store=False)

    def _get_print_name_expression(self):
        """Get the actual Python expression based on pattern selection
        Note: Expressions must be compatible with safe_eval which doesn't support hasattr, time module, etc.
        """
        self.ensure_one()

        if self.print_name_pattern == 'doc_name':
            return "object.name or 'Document'"
        elif self.print_name_pattern == 'doc_customer':
            return "(object.name or 'Document') + ' - ' + (object.partner_id.name or 'Customer')"
        elif self.print_name_pattern == 'doc_customer_ref':
            return "(object.name or 'Document') + ' - ' + (object.partner_id.name or 'Customer') + (((' (' + object.client_order_ref + ')') if object.client_order_ref else ''))"
        elif self.print_name_pattern == 'doc_customer_ref_date':
            # Simplified version without hasattr - safe_eval doesn't support it
            return "(object.name or 'Document') + ' - ' + (object.partner_id.name or 'Customer') + (((' (' + object.client_order_ref + ')') if object.client_order_ref else '')) + ((' - ' + str(object.date_order.date())) if object.date_order else '')"
        elif self.print_name_pattern == 'customer_doc':
            return "(object.partner_id.name or 'Customer') + ' - ' + (object.name or 'Document')"
        elif self.print_name_pattern == 'doc_date':
            # Simplified version without hasattr
            return "(object.name or 'Document') + ((' - ' + str(object.date_order.date())) if object.date_order else '')"
        elif self.print_name_pattern == 'custom':
            return self.print_name_expression or "(object.name or 'Document')"
        else:
            return "(object.name or 'Document') + ' - ' + (object.partner_id.name or 'Customer')"

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
            'footer_show_shape', 'footer_shape_opacity', 'footer_bank_details_show',
            'paper_size', 'paper_orientation'  # Paper settings also trigger regeneration
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

                # Regenerate QWeb templates
                template._create_qweb_template()

        # If paper size/orientation changed, update paperformat
        if 'paper_size' in vals or 'paper_orientation' in vals:
            for template in self:
                if template.report_action_id:
                    # Update paperformat
                    paper_format_name = 'A4' if template.paper_size == 'a4' else 'Letter'
                    orientation = 'Portrait' if template.paper_orientation == 'portrait' else 'Landscape'
                    paperformat_name = f'VPA {paper_format_name} {orientation}'

                    # Find or create the new paperformat
                    paperformat = self.env['report.paperformat'].search([
                        ('name', '=', paperformat_name),
                    ], limit=1)

                    if not paperformat:
                        paperformat = self.env['report.paperformat'].create({
                            'name': paperformat_name,
                            'format': paper_format_name,
                            'orientation': orientation,
                            'margin_top': 0,
                            'margin_bottom': 0,
                            'margin_left': 0,
                            'margin_right': 0,
                            'header_spacing': 0,
                            'dpi': 96,
                        })

                    # Update report action to use new paperformat
                    template.report_action_id.write({'paperformat_id': paperformat.id})

        # Update report action name or print_report_name if changed
        if 'name' in vals or 'print_name_pattern' in vals or 'print_name_expression' in vals:
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

        # Get or create paperformat with zero margins based on template settings
        paper_format_name = 'A4' if self.paper_size == 'a4' else 'Letter'
        orientation = 'Portrait' if self.paper_orientation == 'portrait' else 'Landscape'

        paperformat_name = f'VPA {paper_format_name} {orientation}'

        paperformat = self.env['report.paperformat'].search([
            ('name', '=', paperformat_name),
        ], limit=1)

        paperformat_values = {
            'name': paperformat_name,
            'format': paper_format_name,
            'orientation': orientation,
            'margin_top': 0,
            'margin_bottom': 0,
            'margin_left': 0,
            'margin_right': 0,
            'header_spacing': 0,
            'dpi': 96,
        }

        if not paperformat:
            paperformat = self.env['report.paperformat'].create(paperformat_values)
        else:
            # Update existing paperformat to ensure zero margins
            paperformat.write(paperformat_values)

        # Get print name expression based on pattern selection
        print_name_expr = self._get_print_name_expression()

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
            # Get print name expression based on pattern selection
            print_name_expr = self._get_print_name_expression()

            self.report_action_id.write({
                'name': self.name,
                'print_report_name': print_name_expr,
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

        # Always use custom colors from template settings
        return {
            'header_bg': self.table_header_bg_color or preset['header_bg'],
            'header_text': self.table_header_text_color or preset['header_text'],
            'border': self.table_border_color or preset['border'],
            'alt_row': self.table_row_alt_bg or preset['alt_row'],
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

        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"Starting _create_qweb_template for template {self.id}: {self.name}")

        # Determine which document template to call based on document type
        document_template_map = {
            'quotation': 'sale.report_saleorder_document',
            'sale_order': 'sale.report_saleorder_document',
            'invoice': 'account.report_invoice_document',
            'bill': 'account.report_invoice_document',
        }

        doc_template = document_template_map.get(self.document_type, 'sale.report_saleorder_document')
        _logger.info(f"Document type: {self.document_type}, Using template: {doc_template}")

        # Create standalone VPA report template without hijacking global web.external_layout
        # This allows other document layouts to work normally while VPA templates appear as separate print actions

        # For sale orders, set up address/info blocks and render document
        if self.document_type in ['quotation', 'sale_order']:
            if self.hide_odoo_header:
                # Custom header: Set address and information_block for VPA external layout
                main_template_arch = '''<t t-name="vpa_document_layout.report_template_{template_id}">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="doc">
            <t t-set="doc" t-value="doc.with_context(lang=doc.partner_id.lang, vpa_template_id={template_id})" />
            <t t-set="address">
                <strong><span t-field="doc.partner_id.name"/></strong><br/>
                <div t-field="doc.partner_id" t-options='{{"widget": "contact", "fields": ["address"], "no_marker": True}}'/>
            </t>
            <t t-set="information_block">
                <div t-if="doc.date_order">
                    <strong t-if="doc.state in ['draft', 'sent']">Quotation Date:</strong>
                    <strong t-else="">Order Date:</strong>
                    <span t-field="doc.date_order" t-options='{{"widget": "date"}}'/>
                </div>
                <div t-if="doc.validity_date and doc.state in ['draft', 'sent']" class="mt-2">
                    <strong>Expiration:</strong>
                    <span t-field="doc.validity_date" t-options='{{"widget": "date"}}'/>
                </div>
                <div t-if="doc.user_id.name" class="mt-2">
                    <strong>Salesperson:</strong>
                    <span t-field="doc.user_id"/>
                </div>
            </t>
            <t t-set="layout_document_title">
                <t t-if="doc.state in ['draft','sent']">Quotation # </t>
                <t t-elif="doc.state in ['sale','done']">Order # </t>
                <t t-elif="doc.state == 'cancel'">Cancelled Order # </t>
                <span t-field="doc.name"/>
            </t>
            <t t-call="vpa_document_layout.external_layout_vpa_template_{template_id}">
                <!-- Order Lines Table -->
                <t t-set="display_discount" t-value="any(line.discount for line in doc.order_line)"/>
                <t t-set="display_taxes" t-value="True"/>
                <t t-set="lines_to_report" t-value="doc._get_order_lines_to_report()"/>

                <table class="table table-sm o_main_table">
                    <thead>
                        <tr>
                            <th name="th_description" class="text-start">Description</th>
                            <th name="th_quantity" class="text-end">Quantity</th>
                            <th name="th_priceunit" class="text-end">Unit Price</th>
                            <th name="th_discount" t-if="display_discount" class="text-end">Disc.%</th>
                            <th name="th_taxes" t-if="display_taxes" class="text-end">Taxes</th>
                            <th name="th_subtotal" class="text-end">Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        <t t-foreach="lines_to_report" t-as="line">
                            <tr t-if="line.display_type == \'line_section\'" class="fw-bold o_line_section">
                                <td colspan="99"><span t-field="line.name"/></td>
                            </tr>
                            <tr t-elif="line.display_type == \'line_note\'" class="fst-italic o_line_note">
                                <td colspan="99"><span t-field="line.name"/></td>
                            </tr>
                            <tr t-else="">
                                <td><span t-field="line.name"/></td>
                                <td class="text-end"><span t-field="line.product_uom_qty"/></td>
                                <td class="text-end"><span t-field="line.price_unit"/></td>
                                <td t-if="display_discount" class="text-end"><span t-field="line.discount"/></td>
                                <td t-if="display_taxes" class="text-end">
                                    <span t-out="\', \'.join(map(lambda x: x.description or x.name, line.tax_ids))"/>
                                </td>
                                <td class="text-end"><span t-field="line.price_subtotal"/></td>
                            </tr>
                        </t>
                    </tbody>
                </table>

                <!-- Totals -->
                <div class="clearfix" style="clear: both; overflow: auto;">
                    <div id="total" style="float: right; width: 50%%; max-width: 500px; min-width: 300px;">
                        <table class="table table-sm o_total_table">
                            <tr>
                                <td>Untaxed Amount</td>
                                <td class="text-end"><span t-field="doc.amount_untaxed"/></td>
                            </tr>
                            <tr>
                                <td>Taxes</td>
                                <td class="text-end"><span t-field="doc.amount_tax"/></td>
                            </tr>
                            <tr class="border-black">
                                <td><strong>Total</strong></td>
                                <td class="text-end o_price_total"><span t-field="doc.amount_total"/></td>
                            </tr>
                        </table>
                    </div>
                </div>

                <!-- Terms and conditions -->
                <div t-if="doc.note" class="mt-4">
                    <p><strong>Terms and Conditions:</strong></p>
                    <p t-field="doc.note"/>
                </div>
            </t>
        </t>
    </t>
</t>'''.format(template_id=self.id, hide_footer=str(self.hide_odoo_footer).lower())
            else:
                # Use Odoo's standard header: Just call the full document
                main_template_arch = '''<t t-name="vpa_document_layout.report_template_{template_id}">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="doc">
            <t t-set="doc" t-value="doc.with_context(lang=doc.partner_id.lang)" />
            <t t-call="vpa_document_layout.external_layout_vpa_template_{template_id}">
                <t t-call="sale.report_saleorder_document" t-lang="doc.partner_id.lang"/>
            </t>
        </t>
    </t>
</t>'''.format(template_id=self.id)
        else:
            # For other document types, create a simpler template
            main_template_arch = '''<t t-name="vpa_document_layout.report_template_{template_id}">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="doc">
            <t t-call="vpa_document_layout.external_layout_vpa_template_{template_id}">
                <div class="page">
                    <p>VPA Template for {doc_type} (Document structure pending)</p>
                </div>
            </t>
        </t>
    </t>
</t>'''.format(template_id=self.id, doc_type=self.document_type)  # Format with template ID

        # Create the main report template
        _logger.info(f"Creating main template view for template {self.id}")
        main_template = self.env['ir.ui.view'].create({
            'name': f'VPA Report Template {self.id}',
            'type': 'qweb',
            'key': f'vpa_document_layout.report_template_{self.id}',
            'arch': main_template_arch,
        })
        _logger.info(f"Main template created: {main_template.id}")

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
            /* Force zero margins on all PDF page elements */
            @page {
                margin: 0mm !important;
                padding: 0mm !important;
                %s
            }
            * {
                box-sizing: border-box;
            }
            html {
                margin: 0 !important;
                padding: 0 !important;
                width: 100%% !important;
                height: 100%% !important;
            }
            body {
                margin: 0 !important;
                padding: 0 !important;
                width: 100%% !important;
                height: 100%% !important;
            }
            /* Critical: Remove Odoo's default container padding that adds margins */
            .container, .container-fluid {
                padding-right: 0 !important;
                padding-left: 0 !important;
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                margin: 0 !important;
                max-width: none !important;
                width: 100%% !important;
            }
            div.o_background, .o_background {
                margin: 0 !important;
                padding: 0 !important;
                width: 100%% !important;
                background: transparent !important;
            }
            article, .article {
                margin: 0 !important;
                padding: 0 !important;
                width: 100%% !important;
                background: transparent !important;
            }
            .o_report_layout_vpa {
                position: relative;
                width: 100%% !important;
                height: 100%% !important;
                padding: 0 !important;
                margin: 0 !important;
                box-sizing: border-box;
                background: white !important;
            }
            .o_report_layout_vpa .page {
                position: relative;
                z-index: 2;
                width: 100%% !important;
                height: %smm !important;
                padding: 0 !important;
                margin: 0 !important;
                box-sizing: border-box;
                background: white !important;
            }
            .o_report_layout_vpa .page-layout-table {
                width: 100%%;
                height: 100%%;
                border-collapse: collapse;
                border-spacing: 0;
                border: none !important;
            }
            .o_report_layout_vpa .page-layout-table td.content-cell {
                height: 100%%;
                vertical-align: top;
                padding: 18px;
                border: none !important;
            }
            .o_report_layout_vpa .page-layout-table tr {
                border: none !important;
            }
            /* Main product table - ensure visibility in PDF */
            table.o_main_table, .o_report_layout_vpa table.o_main_table {
                border-collapse: collapse !important;
                border-spacing: 0 !important;
                width: 100%% !important;
                border: 2px solid %s !important;
                margin-bottom: 20px !important;
            }
            table.o_main_table thead th, .o_report_layout_vpa table.o_main_table thead th {
                background: %s !important;
                color: %s !important;
                padding: 12px 8px !important;
                font-weight: bold !important;
                border: 1px solid %s !important;
                text-align: left !important;
                %s
            }
            table.o_main_table tbody td, .o_report_layout_vpa table.o_main_table tbody td {
                padding: 10px 8px !important;
                border: 1px solid %s !important;
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
                border: 1px solid #dee2e6 !important;
            }
            .o_report_layout_vpa table.o_total_table td {
                padding: 10px 12px !important;
                border: 1px solid #dee2e6 !important;
                font-size: 10pt !important;
            }
            .o_report_layout_vpa table.o_total_table tr {
                border-bottom: 1px solid #dee2e6 !important;
            }
            .o_report_layout_vpa table.o_total_table tr:last-child {
                border-top: 2px solid #000 !important;
                background-color: #f8f9fa !important;
                font-weight: bold !important;
                font-size: 11pt !important;
            }
            .o_report_layout_vpa table.o_total_table tr:last-child td {
                font-weight: bold !important;
            }
            .o_report_layout_vpa .o_price_total {
                font-weight: bold !important;
                font-size: 12pt !important;
            }
        </style>

        <!-- Page Content Wrapper -->
        <div class="page">
            <!-- Decorative circle - positioned outside page with higher z-index to appear above content -->
            <svg t-if="%s" style="position: absolute; top: -115px; right: -115px; z-index: -1;" width="%s" height="%s" xmlns="http://www.w3.org/2000/svg">
                <circle cx="%s" cy="%s" r="%s" fill="%s" fill-opacity="%s"/>
            </svg>

            <!-- Real HTML table for reliable footer positioning in PDF -->
            <table class="page-layout-table">
                <tr>
                    <td class="content-cell">
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

            <!-- Inline Footer (for Odoo.sh where --footer-html doesn't work) -->
            <div style="position: relative; margin-top: 30px; padding-top: 20px; font-size: 8pt; line-height: 1.5;">
                <!-- Footer Wave Shape -->
                <svg t-if="%s" style="position: absolute; top: 0; left: -18px; width: calc(100%% + 36px); height: 100%%; z-index: 0;" viewBox="0 0 500 228" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M500 228H0V6.52743C26.3323 2.23278 53.3561 0 80.9008 0C256.522 0 410.969 90.7656 500 228Z"
                          fill="%s" fill-opacity="%s"/>
                </svg>

                <!-- Footer Content -->
                <div style="position: relative; z-index: 1; padding: 0;">
                    <!-- Single Column Layout -->
                    <t t-if="%s">
                        <div style="text-align: center;">
                            <t t-if="vpa_template.footer_column_1_title or vpa_template.footer_column_1_content">
                                <span t-if="vpa_template.footer_column_1_title" style="display: block; margin-bottom: 4px; font-size: 8pt; font-weight: bold; color: %s;" t-esc="vpa_template.footer_column_1_title"/>
                                <div t-if="vpa_template.footer_column_1_content" style="color: #666; line-height: 1.6; font-size: 7.5pt;" t-raw="vpa_template.footer_column_1_content"/>
                            </t>
                        </div>
                    </t>

                    <!-- Two Column Layout -->
                    <t t-if="%s">
                        <table style="width: 100%%; border-collapse: collapse;">
                            <tr>
                                <td style="width: 50%%; vertical-align: top; padding: 0 10px;">
                                    <t t-if="vpa_template.footer_column_1_title or vpa_template.footer_column_1_content">
                                        <span t-if="vpa_template.footer_column_1_title" style="display: block; margin-bottom: 4px; font-size: 8pt; font-weight: bold; color: %s;" t-esc="vpa_template.footer_column_1_title"/>
                                        <div t-if="vpa_template.footer_column_1_content" style="color: #666; line-height: 1.6; font-size: 7.5pt;" t-raw="vpa_template.footer_column_1_content"/>
                                    </t>
                                </td>
                                <td style="width: 50%%; vertical-align: top; padding: 0 10px;">
                                    <t t-if="vpa_template.footer_column_2_title or vpa_template.footer_column_2_content">
                                        <span t-if="vpa_template.footer_column_2_title" style="display: block; margin-bottom: 4px; font-size: 8pt; font-weight: bold; color: %s;" t-esc="vpa_template.footer_column_2_title"/>
                                        <div t-if="vpa_template.footer_column_2_content" style="color: #666; line-height: 1.6; font-size: 7.5pt;" t-raw="vpa_template.footer_column_2_content"/>
                                    </t>
                                </td>
                            </tr>
                        </table>
                    </t>

                    <!-- Three Column Layout -->
                    <t t-if="%s">
                        <table style="width: 100%%; border-collapse: collapse;">
                            <tr>
                                <td style="width: 33.33%%; vertical-align: top; padding: 0 10px;">
                                    <t t-if="vpa_template.footer_column_1_title or vpa_template.footer_column_1_content">
                                        <span t-if="vpa_template.footer_column_1_title" style="display: block; margin-bottom: 4px; font-size: 8pt; font-weight: bold; color: %s;" t-esc="vpa_template.footer_column_1_title"/>
                                        <div t-if="vpa_template.footer_column_1_content" style="color: #666; line-height: 1.6; font-size: 7.5pt;" t-raw="vpa_template.footer_column_1_content"/>
                                    </t>
                                </td>
                                <td style="width: 33.33%%; vertical-align: top; padding: 0 10px;">
                                    <t t-if="vpa_template.footer_column_2_title or vpa_template.footer_column_2_content">
                                        <span t-if="vpa_template.footer_column_2_title" style="display: block; margin-bottom: 4px; font-size: 8pt; font-weight: bold; color: %s;" t-esc="vpa_template.footer_column_2_title"/>
                                        <div t-if="vpa_template.footer_column_2_content" style="color: #666; line-height: 1.6; font-size: 7.5pt;" t-raw="vpa_template.footer_column_2_content"/>
                                    </t>
                                </td>
                                <td style="width: 33.33%%; vertical-align: top; padding: 0 10px;">
                                    <t t-if="vpa_template.footer_column_3_title or vpa_template.footer_column_3_content">
                                        <span t-if="vpa_template.footer_column_3_title" style="display: block; margin-bottom: 4px; font-size: 8pt; font-weight: bold; color: %s;" t-esc="vpa_template.footer_column_3_title"/>
                                        <div t-if="vpa_template.footer_column_3_content" style="color: #666; line-height: 1.6; font-size: 7.5pt;" t-raw="vpa_template.footer_column_3_content"/>
                                    </t>
                                </td>
                            </tr>
                        </table>
                    </t>
                </div>
            </div>
                    </td><!-- Close content-cell -->
                </tr>
            </table><!-- Close page-layout-table -->
        </div><!-- Close page -->
    </div><!-- Close article -->
</t>'''

        # NOTE: Footer can be rendered either:
        # - Inline (Odoo.sh - where --footer-html doesn't work)
        # - Via --footer-html (other environments - better page break handling)

        # Get table styles
        table_styles = self._get_table_styles()

        # Finalize arch_content with all parameters (43 total - with inline footer)
        arch_content = arch_content % (
            self.id,
            self.id,
            self.primary_accent_color,
            self.secondary_accent_color,
            page_size_css,  # @page size
            page_height,  # Page height for layout
            table_styles['border'],  # Table border (2px solid)
            table_styles['header_bg'],  # Table header background (thead th)
            table_styles['header_text'],  # Table header text color (thead th)
            table_styles['border'],  # Table header th border color
            table_styles['header_border_bottom'] if table_styles['header_border_bottom'] != 'none' else '',  # Header border bottom
            table_styles['border'],  # Table body td border color
            table_styles['alt_row'],  # Alternate row background
            str(self.header_show_circle).lower(),  # Decorative circle show
            self.header_circle_size,  # Circle width
            self.header_circle_size,  # Circle height
            self.header_circle_size / 2,  # Circle cx
            self.header_circle_size / 2,  # Circle cy
            self.header_circle_size / 2,  # Circle radius
            self.primary_accent_color,  # Circle fill color
            self.header_circle_opacity,  # Circle opacity
            self.primary_accent_color,  # Header border bottom color
            self.header_logo_alignment,  # Logo alignment
            self._get_logo_style(),  # Logo style
            self.header_company_info_alignment,  # Company info alignment
            self.header_company_info_color,  # Company info div color
            self.header_company_info_color,  # Company info span color (custom HTML)
            self.header_company_info_color,  # Company info span color (company_details)
            self.header_company_info_color,  # Company info span color (partner_id)
            self.primary_accent_color,  # Document title color
            # Footer parameters (inline footer for Odoo.sh)
            str(self.footer_show_shape).lower(),  # Footer wave shape show
            self.secondary_accent_color,  # Footer wave fill color
            self.footer_shape_opacity,  # Footer wave opacity
            str(self.footer_layout == 'single').lower(),  # Single column layout
            self.primary_accent_color,  # Footer column title color (single)
            str(self.footer_layout == 'two_col').lower(),  # Two column layout
            self.primary_accent_color,  # Footer column 1 title color (two col)
            self.primary_accent_color,  # Footer column 2 title color (two col)
            str(self.footer_layout == 'three_col').lower(),  # Three column layout
            self.primary_accent_color,  # Footer column 1 title color (three col)
            self.primary_accent_color,  # Footer column 2 title color (three col)
            self.primary_accent_color,  # Footer column 3 title color (three col)
        )

        _logger.info(f"Creating external layout view for template {self.id}")
        layout_template = self.env['ir.ui.view'].create({
            'name': f'VPA External Layout {self.id}',
            'type': 'qweb',
            'key': f'vpa_document_layout.external_layout_vpa_template_{self.id}',
            'arch': arch_content,
        })
        _logger.info(f"External layout created: {layout_template.id}")
        _logger.info(f"Successfully created all templates for {self.id}")

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

        # Get the first available document of this type WITH lines/items
        domain = [('company_id', '=', self.company_id.id)]

        # Add line check based on model
        if model == 'sale.order':
            domain.append(('order_line', '!=', False))
        elif model == 'account.move':
            domain.append(('invoice_line_ids', '!=', False))
        elif model == 'purchase.order':
            domain.append(('order_line', '!=', False))
        elif model == 'stock.picking':
            domain.append(('move_ids', '!=', False))
        elif model == 'mrp.production':
            domain.append(('move_raw_ids', '!=', False))

        sample = self.env[model].search(domain, limit=1)
        return sample if sample else False

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

    def action_preview_footer(self):
        """Open footer preview in new tab"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/vpa/template/preview_footer/{self.id}',
            'target': 'new',
        }

    def action_preview_template(self):
        """Download PDF preview of this template"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/vpa/template/preview/pdf/{self.id}',
            'target': 'self',
        }
