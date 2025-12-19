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
        ('doc_name', 'Document Number-Abbrev (e.g., S00001-SQ)'),
        ('doc_customer', 'Document-Abbrev - Customer (e.g., S00001-SQ - Deco Addict)'),
        ('doc_customer_ref', 'Document-Abbrev - Customer (Ref) (e.g., S00001-SQ - Deco Addict (REF123))'),
        ('doc_customer_ref_date', 'Document-Abbrev - Customer (Ref) - Date (e.g., S00001-SQ - Deco Addict (REF123) - 2025-01-15)'),
        ('customer_doc', 'Customer - Document-Abbrev (e.g., Deco Addict - S00001-SQ)'),
        ('doc_date', 'Document-Abbrev - Date (e.g., S00001-SQ - 2025-01-15)'),
        ('custom', 'Custom Expression'),
    ], string='PDF Filename Pattern', default='doc_customer_ref', required=True,
       help='Choose how the PDF filename will appear when downloaded. Abbrev = your 2-4 letter abbreviation.')

    print_name_expression = fields.Char(
        string='Custom Filename Expression',
        help='Python expression for PDF filename. Available: object (document record). Example: object.name + " - " + object.partner_id.name'
    )

    document_abbreviation = fields.Char(
        string='Document Abbreviation',
        size=4,
        help='2-4 letter abbreviation for this document type (e.g., SQ for Sales Quote, PS for Production Summary)'
    )

    @api.onchange('document_type')
    def _onchange_document_type_abbreviation(self):
        """Set default abbreviation based on document type"""
        abbreviation_map = {
            'quotation': 'SQ',
            'sale_order': 'SO',
            'sale_production': 'PS',
            'invoice': 'INV',
            'bill': 'BILL',
            'purchase_order': 'PO',
            'delivery': 'DO',
            'picking': 'PICK',
            'manufacturing_order': 'MO',
        }
        if self.document_type and not self.document_abbreviation:
            self.document_abbreviation = abbreviation_map.get(self.document_type, '')

    @api.depends('print_name_pattern', 'print_name_expression', 'document_abbreviation')
    def _compute_print_name_preview(self):
        """Show preview of what the filename will look like"""
        for record in self:
            abbrev = record.document_abbreviation or 'DOC'
            # Format: S00001-SQ - Customer Name (Ref).pdf
            if record.print_name_pattern == 'doc_name':
                record.print_name_preview = f'S00001-{abbrev}.pdf'
            elif record.print_name_pattern == 'doc_customer':
                record.print_name_preview = f'S00001-{abbrev} - Deco Addict.pdf'
            elif record.print_name_pattern == 'doc_customer_ref':
                record.print_name_preview = f'S00001-{abbrev} - Deco Addict (REF123).pdf'
            elif record.print_name_pattern == 'doc_customer_ref_date':
                record.print_name_preview = f'S00001-{abbrev} - Deco Addict (REF123) - 2025-01-15.pdf'
            elif record.print_name_pattern == 'customer_doc':
                record.print_name_preview = f'Deco Addict - S00001-{abbrev}.pdf'
            elif record.print_name_pattern == 'doc_date':
                record.print_name_preview = f'S00001-{abbrev} - 2025-01-15.pdf'
            elif record.print_name_pattern == 'custom':
                record.print_name_preview = 'Custom expression...'
            else:
                record.print_name_preview = ''

    print_name_preview = fields.Char(string='Filename Preview', compute='_compute_print_name_preview', store=False)

    def _get_print_name_expression(self):
        """Get the actual Python expression based on pattern selection
        Note: Expressions must be compatible with safe_eval which doesn't support hasattr, time module, etc.
        Format: S00001-SQ - Customer Name (Ref).pdf
        """
        self.ensure_one()

        # Get abbreviation - will be embedded as literal string in the expression
        abbrev = self.document_abbreviation or 'DOC'

        if self.print_name_pattern == 'doc_name':
            # S00001-SQ
            return f"(object.name or 'Document') + '-{abbrev}'"
        elif self.print_name_pattern == 'doc_customer':
            # S00001-SQ - Customer Name
            return f"(object.name or 'Document') + '-{abbrev} - ' + (object.partner_id.name or 'Customer')"
        elif self.print_name_pattern == 'doc_customer_ref':
            # S00001-SQ - Customer Name (Ref)
            return f"(object.name or 'Document') + '-{abbrev} - ' + (object.partner_id.name or 'Customer') + (((' (' + object.client_order_ref + ')') if object.client_order_ref else ''))"
        elif self.print_name_pattern == 'doc_customer_ref_date':
            # S00001-SQ - Customer Name (Ref) - 2025-01-15
            return f"(object.name or 'Document') + '-{abbrev} - ' + (object.partner_id.name or 'Customer') + (((' (' + object.client_order_ref + ')') if object.client_order_ref else '')) + ((' - ' + str(object.date_order.date())) if object.date_order else '')"
        elif self.print_name_pattern == 'customer_doc':
            # Customer Name - S00001-SQ
            return f"(object.partner_id.name or 'Customer') + ' - ' + (object.name or 'Document') + '-{abbrev}'"
        elif self.print_name_pattern == 'doc_date':
            # S00001-SQ - 2025-01-15
            return f"(object.name or 'Document') + '-{abbrev}' + ((' - ' + str(object.date_order.date())) if object.date_order else '')"
        elif self.print_name_pattern == 'custom':
            return self.print_name_expression or "(object.name or 'Document')"
        else:
            # Default: S00001-SQ - Customer Name (Ref)
            return f"(object.name or 'Document') + '-{abbrev} - ' + (object.partner_id.name or 'Customer') + (((' (' + object.client_order_ref + ')') if object.client_order_ref else ''))"

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
        ('sale_production', 'Sales Production Order'),
        ('quotation_pictures', 'Quotation (Pictures)'),
        ('invoice', 'Invoice'),
        ('bill', 'Vendor Bill'),
        ('purchase_order', 'Purchase Order'),
        ('delivery', 'Delivery Order'),
        ('picking', 'Picking'),
        ('manufacturing_order', 'Manufacturing Order'),
    ], string='Document Type', required=True, help='Which document type this template applies to')

    # Report Title Configuration
    report_title = fields.Char(
        string='Report Title',
        help='Custom title shown on the report header (e.g., "Production Order", "Sales Quote"). Leave empty for default.'
    )

    # Odoo Header/Footer Control
    hide_odoo_header = fields.Boolean(string='Hide Standard Odoo Header', default=True)
    hide_odoo_footer = fields.Boolean(string='Hide Standard Odoo Footer', default=True)

    # Repeating Header (for multi-page documents)
    header_repeat_on_pages = fields.Boolean(
        string='Repeat Header on All Pages',
        default=True,
        help='When enabled, the header (logo + company info) will appear on every page of multi-page documents. '
             'If disabled, the header only appears on the first page.'
    )
    header_height = fields.Char(
        string='Header Height',
        default='30mm',
        help='Height reserved for the header area (e.g., 30mm, 25mm)'
    )

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

    # Footer Settings - Now uses unified footer config
    footer_config_id = fields.Many2one(
        'vpa.footer.config',
        string='Footer Configuration',
        domain="[('company_id', '=', company_id), ('active', '=', True)]",
        help='Select a footer configuration. If not set, the default footer for the document type will be used.'
    )

    # Legacy footer settings (kept for backwards compatibility)
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

    # Template-level Footer Customization (Quick Settings)
    footer_enabled = fields.Boolean(
        string='Show Footer',
        default=True,
        help='Enable or disable the footer on this template'
    )
    footer_show_content = fields.Boolean(
        string='Show Footer Content',
        default=True,
        help='Show the column content in footer. Disable to show only wave shape, message and page numbers.'
    )
    footer_show_page_number = fields.Boolean(
        string='Show Page Number',
        default=True,
        help='Display page number in the footer (e.g., "Page 1 of 3")'
    )
    footer_page_number_format = fields.Selection([
        ('page_of', 'Page X of Y'),
        ('page_only', 'Page X'),
        ('dash', '- X -'),
        ('brackets', '[X/Y]'),
    ], string='Page Number Format', default='page_of')
    footer_message_type = fields.Selection([
        ('none', 'No Message'),
        ('auto_generated', 'This document was automatically generated'),
        ('internal', 'Internal Document - Confidential'),
        ('draft', 'DRAFT - Not for Distribution'),
        ('quote_validity', 'This quotation is valid for 30 days'),
        ('thank_you', 'Thank you for your business'),
        ('custom', 'Custom Message'),
    ], string='Footer Message', default='none',
       help='Predefined message to display in footer with typewriter font')
    footer_custom_message = fields.Char(
        string='Custom Footer Message',
        help='Your custom message (displayed when "Custom Message" is selected)'
    )

    # Import footer data from another template (stored so button action can access it)
    import_footer_from_template = fields.Many2one(
        'vpa.document.template',
        string='Import Footer From Template',
        domain="[('company_id', '=', company_id), ('active', '=', True), ('id', '!=', id)]",
        help='Select another template to import its footer data into this template'
    )

    # Report Action Reference (auto-created)
    report_action_id = fields.Many2one('ir.actions.report', string='Report Action', readonly=True, ondelete='cascade')

    # Default Template Selection
    is_default_print = fields.Boolean(
        string='Set as Default Print Template',
        default=False,
        help='When enabled, this template will be used by default for printing this document type'
    )
    is_default_email = fields.Boolean(
        string='Set as Default Email Template',
        default=False,
        help='When enabled, this template will be used by default when sending this document type via email'
    )

    # Preview field (like the old VPA config)
    preview = fields.Html(compute='_compute_preview', sanitize=False)

    # Odoo 19 Constraint syntax (nested class)
    class Constraint(models.Constraint):
        _constraint_name = 'name_company_doctype_uniq'
        _definition = 'UNIQUE(name, company_id, document_type)'
        _message = 'A template with this name already exists for this company and document type. Please choose a different name.'

    @api.depends('name', 'primary_accent_color', 'secondary_accent_color',
                 'header_logo_alignment', 'header_logo_width', 'header_logo_height', 'header_logo_aspect_ratio',
                 'header_company_info_alignment', 'header_company_details_html', 'header_company_info_color',
                 'header_show_circle', 'header_circle_size', 'header_circle_opacity',
                 'table_style', 'table_header_bg_color', 'table_header_text_color', 'table_border_color', 'table_row_alt_bg',
                 'footer_enabled', 'footer_show_page_number', 'footer_page_number_format',
                 'footer_message_type', 'footer_custom_message',
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
        # Handle default template selection - ensure only one default per company/document_type
        if vals.get('is_default_print') or vals.get('is_default_email'):
            for template in self:
                # If setting as default print, unset other defaults
                if vals.get('is_default_print'):
                    other_defaults = self.env['vpa.document.template'].search([
                        ('id', '!=', template.id),
                        ('company_id', '=', template.company_id.id),
                        ('document_type', '=', template.document_type),
                        ('is_default_print', '=', True)
                    ])
                    if other_defaults:
                        other_defaults.write({'is_default_print': False})

                # If setting as default email, unset other defaults
                if vals.get('is_default_email'):
                    other_defaults = self.env['vpa.document.template'].search([
                        ('id', '!=', template.id),
                        ('company_id', '=', template.company_id.id),
                        ('document_type', '=', template.document_type),
                        ('is_default_email', '=', True)
                    ])
                    if other_defaults:
                        other_defaults.write({'is_default_email': False})

        result = super(VPADocumentTemplate, self).write(vals)

        # Skip template regeneration during module install/upgrade to avoid locks
        if self.env.context.get('install_mode') or self.env.context.get('module'):
            return result

        # Fields that require template regeneration
        template_fields = [
            'header_logo_alignment', 'header_logo_width', 'header_logo_height',
            'header_logo_aspect_ratio', 'header_company_info_alignment', 'header_company_details_html',
            'header_show_circle', 'header_circle_size', 'header_circle_opacity',
            'primary_accent_color', 'secondary_accent_color',
            'footer_show_shape', 'footer_shape_opacity', 'footer_bank_details_show',
            'footer_layout', 'footer_column_1_title', 'footer_column_1_content',
            'footer_column_2_title', 'footer_column_2_content',
            'footer_column_3_title', 'footer_column_3_content',
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
        if 'name' in vals or 'print_name_pattern' in vals or 'print_name_expression' in vals or 'document_abbreviation' in vals:
            for template in self:
                if template.report_action_id:
                    template._update_report_action()

        # If document_type changed, update the report binding model and regenerate template
        if 'document_type' in vals:
            model_map = {
                'quotation': 'sale.order',
                'sale_order': 'sale.order',
                'sale_production': 'sale.order',
                'invoice': 'account.move',
                'bill': 'account.move',
                'purchase_order': 'purchase.order',
                'delivery': 'stock.picking',
                'picking': 'stock.picking',
                'manufacturing_order': 'mrp.production',
            }
            for template in self:
                new_model = model_map.get(template.document_type, 'sale.order')
                if template.report_action_id:
                    # Update report action binding
                    template.report_action_id.write({
                        'model': new_model,
                        'binding_model_id': self.env['ir.model']._get(new_model).id,
                    })
                # Delete old QWeb views and regenerate
                existing_views = self.env['ir.ui.view'].search([
                    '|', '|',
                    ('key', 'like', f'%template_{template.id}%'),
                    ('key', 'like', f'%inherit_{template.id}%'),
                    ('name', 'like', f'%{template.id}')
                ])
                existing_views.unlink()
                template._create_qweb_template()

        return result

    def unlink(self):
        """Delete template and its report action"""
        for template in self:
            if template.report_action_id:
                template.report_action_id.unlink()
        return super(VPADocumentTemplate, self).unlink()

    @api.model
    def action_cleanup_orphan_reports(self):
        """
        Cleanup orphan VPA report actions that don't have a corresponding template.
        This can happen if templates were deleted directly from the database.
        Call this method to fix duplicate entries in Print menu.
        """
        # Find all VPA report actions (they have report_name starting with 'vpa_document_layout.report_template_')
        orphan_reports = self.env['ir.actions.report'].search([
            ('report_name', 'like', 'vpa_document_layout.report_template_%')
        ])

        # Get all template IDs that have report actions
        template_report_ids = self.search([]).mapped('report_action_id').ids

        # Find orphan reports (not linked to any template)
        orphan_count = 0
        for report in orphan_reports:
            if report.id not in template_report_ids:
                _logger.info(f"Deleting orphan VPA report action: {report.name} (ID: {report.id})")
                report.unlink()
                orphan_count += 1

        if orphan_count:
            _logger.info(f"Cleaned up {orphan_count} orphan VPA report action(s)")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Cleanup Complete'),
                'message': _('Removed %s orphan report action(s) from the print menu.') % orphan_count,
                'type': 'success' if orphan_count else 'info',
                'sticky': False,
            }
        }

    def _create_report_action(self):
        """Create a new report action for this template"""
        self.ensure_one()

        # Determine model based on document type
        model_map = {
            'quotation': 'sale.order',
            'sale_order': 'sale.order',
            'sale_production': 'sale.order',
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

    def action_import_footer_data(self):
        """Open wizard to import footer data from another template"""
        self.ensure_one()
        return {
            'name': _('Import Footer Data'),
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.import.footer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.id,
            }
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
                # Styled to match Production Summary template
                main_template_arch = '''<t t-name="vpa_document_layout.report_template_{template_id}">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="doc">
            <t t-set="doc" t-value="doc.with_context(lang=doc.partner_id.lang, vpa_template_id={template_id})" />
            <t t-set="vpa_template" t-value="env['vpa.document.template'].browse({template_id})"/>
            <t t-set="primary_color" t-value="vpa_template.primary_accent_color or '#DC143C'"/>
            <t t-set="address">
                <div t-att-style="'font-family: Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 6px; color: ' + (vpa_template.primary_accent_color or '#DC143C')">CUSTOMER DETAILS</div>
                <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                    <div><strong><span t-field="doc.partner_id.name"/></strong></div>
                    <div t-field="doc.partner_id" t-options='{{"widget": "contact", "fields": ["address"], "no_marker": True}}'/>
                </div>
            </t>
            <t t-set="information_block">
                <div t-att-style="'font-family: Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 6px; color: ' + (vpa_template.primary_accent_color or '#DC143C')">ORDER INFO</div>
                <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                    <div t-if="doc.date_order">
                        <strong t-if="doc.state in ['draft', 'sent']">Quotation Date:</strong>
                        <strong t-else="">Order Date:</strong>
                        <span t-field="doc.date_order" t-options='{{"widget": "date"}}'/>
                    </div>
                    <div t-if="doc.validity_date and doc.state in ['draft', 'sent']" style="margin-top: 4px;">
                        <strong>Expiration:</strong>
                        <span t-field="doc.validity_date" t-options='{{"widget": "date"}}'/>
                    </div>
                    <div t-if="doc.client_order_ref" style="margin-top: 4px;">
                        <strong>Customer Reference:</strong>
                        <span t-field="doc.client_order_ref"/>
                    </div>
                    <div t-if="doc.user_id.name" style="margin-top: 4px;">
                        <strong>Salesperson:</strong>
                        <span t-field="doc.user_id"/>
                    </div>
                </div>
            </t>
            <t t-set="layout_document_title">
                <t t-if="doc.state in ['draft','sent']">Quotation # </t>
                <t t-elif="doc.state in ['sale','done']">Order # </t>
                <t t-elif="doc.state == 'cancel'">Cancelled Order # </t>
                <span t-field="doc.name"/>
            </t>
            <t t-call="vpa_document_layout.external_layout_vpa_template_{template_id}">
                <!-- Inline Styles matching Production Summary -->
                <style>
                    .vpa-quote-order {{
                        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                        font-size: 12px;
                        color: #333;
                    }}
                    /* Table Card Container */
                    .vpa-table-card {{
                        background: linear-gradient(135deg, #fffafa 0%%, white 100%%);
                        border-left: 3px solid <t t-out="primary_color"/>;
                        border-radius: 5px;
                        padding: 6px;
                        margin-bottom: 10px;
                        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
                    }}
                    .vpa-table-card table {{
                        width: 100%%;
                        border-collapse: collapse;
                        border: none !important;
                    }}
                    .vpa-table-card th {{
                        background: transparent;
                        color: <t t-out="primary_color"/>;
                        font-weight: 600;
                        text-transform: uppercase;
                        font-size: 10px;
                        padding: 5px 4px;
                        border: none !important;
                        border-bottom: 1px solid #f0f0f0 !important;
                        border-right: 1px solid #f0f0f0 !important;
                        letter-spacing: 0.3px;
                    }}
                    .vpa-table-card th:last-child {{
                        border-right: none !important;
                    }}
                    .vpa-table-card td {{
                        padding: 4px 4px;
                        font-size: 11px;
                        color: #333;
                        border: none !important;
                        border-bottom: 1px solid #f8f8f8 !important;
                        border-right: 1px solid #f8f8f8 !important;
                        line-height: 1.3;
                    }}
                    .vpa-table-card td:last-child {{
                        border-right: none !important;
                    }}
                    .vpa-table-card tbody tr:last-child td {{
                        border-bottom: none !important;
                    }}
                    /* Section Header in Table */
                    .vpa-section-header {{
                        color: <t t-out="primary_color"/>;
                        font-size: 11px;
                        font-weight: 600;
                        text-transform: uppercase;
                        letter-spacing: 0.4px;
                        margin: 6px 6px 4px 6px;
                        padding-bottom: 3px;
                        border-bottom: 1px solid #f0f0f0;
                    }}
                    /* Section Row (category divider) */
                    .vpa-section-row td {{
                        background: #f0f0f0;
                        font-weight: 700;
                        padding: 6px 4px;
                        color: #666;
                        font-size: 12px;
                        border-bottom: 1px solid #ddd !important;
                    }}
                    /* Note Row */
                    .vpa-note-row td {{
                        padding: 4px 12px;
                        font-style: italic;
                        color: #555;
                        font-size: 11px;
                        background: #fafafa;
                        border-bottom: 1px solid #f0f0f0 !important;
                    }}
                    /* Badges */
                    .vpa-qty-badge {{
                        display: inline-block;
                        background: white;
                        color: <t t-out="primary_color"/>;
                        padding: 2px 6px;
                        border-radius: 2px;
                        font-weight: 600;
                        font-size: 11px;
                        border: 1px solid <t t-out="primary_color"/>;
                    }}
                    .vpa-amount-badge {{
                        display: inline-block;
                        background: <t t-out="primary_color"/>;
                        color: white;
                        padding: 2px 8px;
                        border-radius: 2px;
                        font-weight: 600;
                        font-size: 11px;
                    }}
                    /* Product Details */
                    .vpa-product-code {{
                        color: #777;
                        font-size: 10px;
                    }}
                    /* Total Card */
                    .vpa-total-card {{
                        background: linear-gradient(135deg, #fffafa 0%%, white 100%%);
                        border-left: 3px solid <t t-out="primary_color"/>;
                        padding: 10px;
                        border-radius: 5px;
                        margin: 10px 0;
                        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
                    }}
                    .vpa-total-card table {{
                        width: 100%%;
                        border-collapse: collapse;
                    }}
                    .vpa-total-card td {{
                        padding: 6px 8px;
                        font-size: 11px;
                        border: none !important;
                    }}
                    .vpa-total-card tr.vpa-total-row td {{
                        border-top: 2px solid <t t-out="primary_color"/> !important;
                        padding-top: 10px;
                    }}
                    .vpa-total-label {{
                        font-size: 11px;
                        color: #666;
                    }}
                    .vpa-total-value {{
                        font-size: 11px;
                        color: #333;
                        font-weight: 500;
                    }}
                    .vpa-grand-total-label {{
                        font-size: 14px;
                        color: <t t-out="primary_color"/>;
                        font-weight: 600;
                    }}
                    .vpa-grand-total-value {{
                        font-size: 18px;
                        color: <t t-out="primary_color"/>;
                        font-weight: 600;
                    }}
                    /* Notes Section */
                    .vpa-notes-section {{
                        background: #f9f9f9;
                        border: 1px solid #e0e0e0;
                        border-radius: 5px;
                        padding: 10px;
                        margin: 10px 0;
                        page-break-inside: avoid;
                    }}
                    .vpa-notes-title {{
                        color: <t t-out="primary_color"/>;
                        margin: 0 0 6px 0;
                        font-size: 11px;
                        font-weight: 600;
                    }}
                </style>

                <div class="vpa-quote-order">
                    <!-- Order Lines Table -->
                    <t t-set="display_discount" t-value="any(line.discount for line in doc.order_line)"/>
                    <t t-set="lines_to_report" t-value="doc._get_order_lines_to_report()"/>

                    <div class="vpa-table-card">
                        <div class="vpa-section-header">ORDER DETAILS</div>
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 5%%; text-align: center;">NO.</th>
                                    <th style="width: 40%%;">DESCRIPTION</th>
                                    <th style="width: 10%%; text-align: center;">QTY</th>
                                    <th style="width: 8%%; text-align: center;">UNIT</th>
                                    <th style="width: 12%%; text-align: right;">UNIT PRICE</th>
                                    <th t-if="display_discount" style="width: 8%%; text-align: center;">DISC.%%</th>
                                    <th style="width: 17%%; text-align: right;">AMOUNT</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-set="line_num" t-value="0"/>
                                <t t-foreach="lines_to_report" t-as="line">
                                    <!-- Section Headers -->
                                    <t t-if="line.display_type == 'line_section'">
                                        <tr class="vpa-section-row">
                                            <td t-att-colspan="'7' if display_discount else '6'"><span t-field="line.name"/></td>
                                        </tr>
                                    </t>
                                    <!-- Note Lines -->
                                    <t t-elif="line.display_type == 'line_note'">
                                        <tr class="vpa-note-row">
                                            <td t-att-colspan="'7' if display_discount else '6'"><span t-field="line.name"/></td>
                                        </tr>
                                    </t>
                                    <!-- Regular Product Lines -->
                                    <t t-else="">
                                        <t t-set="line_num" t-value="line_num + 1"/>
                                        <tr>
                                            <td style="text-align: center; color: #666; font-size: 10pt;"><t t-out="line_num"/></td>
                                            <td>
                                                <div style="font-weight: 500; color: #333; font-size: 10pt;">
                                                    <span t-field="line.name"/>
                                                </div>
                                            </td>
                                            <td style="text-align: center; font-size: 10pt;">
                                                <span class="vpa-qty-badge"><t t-out="int(line.product_uom_qty) if line.product_uom_qty == int(line.product_uom_qty) else round(line.product_uom_qty, 2)"/></span>
                                            </td>
                                            <td style="text-align: center; color: #666; font-size: 10pt;">
                                                <span t-field="line.product_uom_id"/>
                                            </td>
                                            <td style="text-align: right; font-size: 10pt;">
                                                <t t-out="'{{:,.2f}}'.format(line.price_unit)"/>
                                            </td>
                                            <td t-if="display_discount" style="text-align: center; font-size: 10pt;">
                                                <span t-field="line.discount"/><t t-out="'%'"/>
                                            </td>
                                            <td style="text-align: right; font-size: 10pt;">
                                                <span class="vpa-amount-badge"><span t-field="line.price_subtotal"/></span>
                                            </td>
                                        </tr>
                                    </t>
                                </t>
                            </tbody>
                        </table>
                    </div>

                    <!-- Totals Card -->
                    <div style="overflow: hidden;">
                        <div class="vpa-total-card" style="width: 350px; float: right;">
                            <table>
                                <tr>
                                    <td style="text-align: right; width: 60%%;">
                                        <span class="vpa-total-label">Subtotal:</span>
                                    </td>
                                    <td style="text-align: right; width: 40%%;">
                                        <span class="vpa-total-value"><span t-field="doc.amount_untaxed"/></span>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="text-align: right;">
                                        <span class="vpa-total-label">Taxes:</span>
                                    </td>
                                    <td style="text-align: right;">
                                        <span class="vpa-total-value"><span t-field="doc.amount_tax"/></span>
                                    </td>
                                </tr>
                                <tr class="vpa-total-row">
                                    <td style="text-align: right;">
                                        <span class="vpa-grand-total-label">Total:</span>
                                    </td>
                                    <td style="text-align: right;">
                                        <span class="vpa-grand-total-value"><span t-field="doc.amount_total"/></span>
                                    </td>
                                </tr>
                            </table>
                        </div>
                    </div>

                    <!-- Terms and Conditions -->
                    <t t-if="doc.note">
                        <div class="vpa-notes-section">
                            <div class="vpa-notes-title">TERMS AND CONDITIONS:</div>
                            <div style="font-size: 10px; color: #444; line-height: 1.4;">
                                <span t-field="doc.note"/>
                            </div>
                        </div>
                    </t>
                </div>
            </t>
        </t>
    </t>
</t>'''.format(template_id=self.id)
            else:
                # Use Odoo's standard header: Just call the full document
                # CRITICAL: Include font-size styles INSIDE the template to override Odoo defaults
                main_template_arch = '''<t t-name="vpa_document_layout.report_template_{template_id}">
    <t t-call="web.html_container">
        <style>
            /* VPA Font Size Overrides - MUST be inside template to work */
            table thead th,
            table.table thead th,
            .page table thead th {{
                font-size: 15pt !important;
                padding: 14px 12px !important;
            }}
            table tbody td,
            table.table tbody td,
            .page table tbody td {{
                font-size: 14pt !important;
                padding: 12px !important;
                line-height: 1.5 !important;
            }}
            table tbody tr.o_line_section td {{
                font-size: 16pt !important;
                font-weight: bold !important;
            }}
            #total td, .o_total td {{
                font-size: 14pt !important;
            }}
            #total tr:last-child td, .o_total tr:last-child td {{
                font-size: 16pt !important;
                font-weight: bold !important;
            }}
        </style>
        <t t-foreach="docs" t-as="doc">
            <t t-set="doc" t-value="doc.with_context(lang=doc.partner_id.lang)" />
            <t t-call="vpa_document_layout.external_layout_vpa_template_{template_id}">
                <t t-call="sale.report_saleorder_document" t-lang="doc.partner_id.lang"/>
            </t>
        </t>
    </t>
</t>'''.format(template_id=self.id)
        elif self.document_type == 'manufacturing_order':
            # Manufacturing Order template - wraps standard MRP report
            main_template_arch = '''<t t-name="vpa_document_layout.report_template_{template_id}">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="doc">
            <t t-set="doc" t-value="doc.with_context(vpa_template_id={template_id})" />
            <t t-set="vpa_template" t-value="env['vpa.document.template'].browse({template_id})"/>
            <t t-set="address">
                <t t-if="doc.partner_id">
                    <div t-att-style="'font-family: Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 6px; color: ' + (vpa_template.primary_accent_color or '#DC143C')">CUSTOMER DETAILS</div>
                    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                        <div><strong><span t-field="doc.partner_id.name"/></strong></div>
                        <div t-field="doc.partner_id" t-options='{{"widget": "contact", "fields": ["address"], "no_marker": True}}'/>
                    </div>
                </t>
            </t>
            <t t-set="information_block">
                <div t-att-style="'font-family: Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 6px; color: ' + (vpa_template.primary_accent_color or '#DC143C')">ORDER INFO</div>
                <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                    <div t-if="doc.date_start">
                        <strong>Scheduled Date:</strong>
                        <span t-field="doc.date_start" t-options='{{"widget": "date"}}'/>
                    </div>
                    <div t-if="doc.user_id.name" style="margin-top: 4px;">
                        <strong>Responsible:</strong>
                        <span t-field="doc.user_id"/>
                    </div>
                    <div t-if="doc.origin" style="margin-top: 4px;">
                        <strong>Source:</strong>
                        <span t-field="doc.origin"/>
                    </div>
                </div>
            </t>
            <t t-set="layout_document_title">
                Manufacturing Order # <span t-field="doc.name"/>
            </t>
            <t t-call="vpa_document_layout.external_layout_vpa_template_{template_id}">
                <!-- Product Information -->
                <div class="row mb-4">
                    <div class="col-6">
                        <strong>Product:</strong> <span t-field="doc.product_id"/>
                    </div>
                    <div class="col-3">
                        <strong>Quantity:</strong> <span t-field="doc.product_qty"/> <span t-field="doc.product_uom_id"/>
                    </div>
                    <div class="col-3">
                        <strong>State:</strong> <span t-field="doc.state"/>
                    </div>
                </div>

                <!-- Components Table -->
                <h4 class="mt-4">Components to Consume</h4>
                <table class="table table-sm o_main_table">
                    <thead>
                        <tr>
                            <th class="text-start">Product</th>
                            <th class="text-end">To Consume</th>
                            <th class="text-end">Consumed</th>
                            <th class="text-center">UoM</th>
                        </tr>
                    </thead>
                    <tbody>
                        <t t-foreach="doc.move_raw_ids" t-as="move">
                            <tr>
                                <td><span t-field="move.product_id"/></td>
                                <td class="text-end"><t t-out="int(move.product_uom_qty) if move.product_uom_qty == int(move.product_uom_qty) else round(move.product_uom_qty, 2)"/></td>
                                <td class="text-end"><t t-out="int(move.quantity) if move.quantity == int(move.quantity) else round(move.quantity, 2)"/></td>
                                <td class="text-center"><span t-field="move.product_uom"/></td>
                            </tr>
                        </t>
                    </tbody>
                </table>

                <!-- Work Orders (if any) -->
                <t t-if="doc.workorder_ids">
                    <h4 class="mt-4">Work Orders</h4>
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th class="text-start">Operation</th>
                                <th class="text-start">Work Center</th>
                                <th class="text-end">Expected Duration</th>
                                <th class="text-center">State</th>
                            </tr>
                        </thead>
                        <tbody>
                            <t t-foreach="doc.workorder_ids" t-as="wo">
                                <tr>
                                    <td><span t-field="wo.name"/></td>
                                    <td><span t-field="wo.workcenter_id"/></td>
                                    <td class="text-end"><span t-field="wo.duration_expected"/> min</td>
                                    <td class="text-center"><span t-field="wo.state"/></td>
                                </tr>
                            </t>
                        </tbody>
                    </table>
                </t>

                <!-- Finished Products -->
                <t t-if="doc.move_finished_ids">
                    <h4 class="mt-4">Finished Products</h4>
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th class="text-start">Product</th>
                                <th class="text-end">To Produce</th>
                                <th class="text-end">Produced</th>
                                <th class="text-center">UoM</th>
                            </tr>
                        </thead>
                        <tbody>
                            <t t-foreach="doc.move_finished_ids" t-as="move">
                                <tr>
                                    <td><span t-field="move.product_id"/></td>
                                    <td class="text-end"><t t-out="int(move.product_uom_qty) if move.product_uom_qty == int(move.product_uom_qty) else round(move.product_uom_qty, 2)"/></td>
                                    <td class="text-end"><t t-out="int(move.quantity) if move.quantity == int(move.quantity) else round(move.quantity, 2)"/></td>
                                    <td class="text-center"><span t-field="move.product_uom"/></td>
                                </tr>
                            </t>
                        </tbody>
                    </table>
                </t>
            </t>
        </t>
    </t>
</t>'''.format(template_id=self.id)
        elif self.document_type == 'sale_production':
            # Sales Production Order template - Sale Order with Production Details for factory
            main_template_arch = '''<t t-name="vpa_document_layout.report_template_{template_id}">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="doc">
            <t t-set="doc" t-value="doc.with_context(lang=doc.partner_id.lang, vpa_template_id={template_id})" />
            <t t-set="vpa_template" t-value="env['vpa.document.template'].browse({template_id})"/>
            <t t-set="primary_color" t-value="vpa_template.primary_accent_color or '#DC143C'"/>
            <t t-set="report_title" t-value="vpa_template.report_title or 'Production Order'"/>
            <t t-set="address">
                <div t-att-style="'font-family: Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 6px; color: ' + (vpa_template.primary_accent_color or '#DC143C')">CUSTOMER DETAILS</div>
                <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                    <div><strong><span t-field="doc.partner_id.name"/></strong></div>
                    <div t-field="doc.partner_id" t-options='{{"widget": "contact", "fields": ["address"], "no_marker": True}}'/>
                </div>
            </t>
            <t t-set="information_block">
                <div t-att-style="'font-family: Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 6px; color: ' + (vpa_template.primary_accent_color or '#DC143C')">ORDER INFO</div>
                <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                    <div t-if="doc.date_order">
                        <strong>Order Date:</strong>
                        <span t-field="doc.date_order" t-options='{{"widget": "date"}}'/>
                    </div>
                    <div t-if="doc.commitment_date" style="margin-top: 4px;">
                        <strong>Expected Delivery:</strong>
                        <span t-field="doc.commitment_date" t-options='{{"widget": "date"}}'/>
                    </div>
                    <div t-if="doc.client_order_ref" style="margin-top: 4px;">
                        <strong>Customer Reference:</strong>
                        <span t-field="doc.client_order_ref"/>
                    </div>
                    <div style="margin-top: 4px;">
                        <strong>Status:</strong>
                        <t t-if="doc.state == 'draft'"><span style="color: #6c757d;">Quotation</span></t>
                        <t t-elif="doc.state == 'sent'"><span style="color: #17a2b8;">Sent</span></t>
                        <t t-elif="doc.state == 'sale'"><span style="color: #28a745;">Confirmed</span></t>
                        <t t-elif="doc.state == 'done'"><span style="color: #28a745;">Done</span></t>
                        <t t-elif="doc.state == 'cancel'"><span style="color: #dc3545;">Cancelled</span></t>
                        <t t-else=""><t t-out="dict(doc._fields['state'].selection).get(doc.state, doc.state)"/></t>
                    </div>
                </div>
            </t>
            <t t-set="layout_document_title">
                <t t-out="report_title"/> # <span t-field="doc.name"/>
            </t>
            <t t-call="vpa_document_layout.external_layout_vpa_template_{template_id}">
                <!-- Inline Styles for Sale Production specific elements -->
                <style>
                    .vpa-sale-production {{
                        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                        font-size: 12px;
                        color: #333;
                    }}
                    /* Table Card Container */
                    .vpa-table-card {{
                        background: linear-gradient(135deg, #fffafa 0%%, white 100%%);
                        border-left: 3px solid <t t-out="primary_color"/>;
                        border-radius: 5px;
                        padding: 6px;
                        margin-bottom: 10px;
                        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
                    }}
                    .vpa-table-card table {{
                        width: 100%%;
                        border-collapse: collapse;
                        border: none !important;
                    }}
                    .vpa-table-card th {{
                        background: transparent;
                        color: <t t-out="primary_color"/>;
                        font-weight: 600;
                        text-transform: uppercase;
                        font-size: 10px;
                        padding: 5px 4px;
                        border: none !important;
                        border-bottom: 1px solid #f0f0f0 !important;
                        border-right: 1px solid #f0f0f0 !important;
                        letter-spacing: 0.3px;
                    }}
                    .vpa-table-card th:last-child {{
                        border-right: none !important;
                    }}
                    .vpa-table-card td {{
                        padding: 4px 4px;
                        font-size: 11px;
                        color: #333;
                        border: none !important;
                        border-bottom: 1px solid #f8f8f8 !important;
                        border-right: 1px solid #f8f8f8 !important;
                        line-height: 1.3;
                    }}
                    .vpa-table-card td:last-child {{
                        border-right: none !important;
                    }}
                    .vpa-table-card tbody tr:last-child td {{
                        border-bottom: none !important;
                    }}
                    /* Section Header in Table */
                    .vpa-section-header {{
                        color: <t t-out="primary_color"/>;
                        font-size: 11px;
                        font-weight: 600;
                        text-transform: uppercase;
                        letter-spacing: 0.4px;
                        margin: 6px 6px 4px 6px;
                        padding-bottom: 3px;
                        border-bottom: 1px solid #f0f0f0;
                    }}
                    /* Section Row (category divider) */
                    .vpa-section-row td {{
                        background: #f0f0f0;
                        font-weight: 700;
                        padding: 6px 4px;
                        color: #666;
                        font-size: 12px;
                        border-bottom: 1px solid #ddd !important;
                    }}
                    /* Note Row */
                    .vpa-note-row td {{
                        padding: 4px 12px;
                        font-style: italic;
                        color: #555;
                        font-size: 11px;
                        background: #fafafa;
                        border-bottom: 1px solid #f0f0f0 !important;
                    }}
                    /* Badges */
                    .vpa-qty-badge {{
                        display: inline-block;
                        background: white;
                        color: <t t-out="primary_color"/>;
                        padding: 2px 6px;
                        border-radius: 2px;
                        font-weight: 600;
                        font-size: 11px;
                        border: 1px solid <t t-out="primary_color"/>;
                    }}
                    .vpa-mo-badge {{
                        display: inline-block;
                        background: <t t-out="primary_color"/>;
                        color: white;
                        padding: 2px 6px;
                        border-radius: 6px;
                        font-size: 9px;
                        font-weight: 500;
                        margin: 1px;
                    }}
                    .vpa-mo-pending {{
                        background: transparent;
                        color: #bbb;
                        border: none;
                        font-size: 10px;
                    }}
                    /* Product Details */
                    .vpa-product-details {{
                        font-size: 10px;
                        color: #666;
                        margin-top: 2px;
                        line-height: 1.3;
                    }}
                    .vpa-product-code {{
                        color: #777;
                        font-size: 10px;
                    }}
                    /* Total Card */
                    .vpa-total-card {{
                        background: linear-gradient(135deg, #fffafa 0%%, white 100%%);
                        border-left: 3px solid <t t-out="primary_color"/>;
                        padding: 10px;
                        border-radius: 5px;
                        margin: 10px 0;
                        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
                    }}
                    .vpa-total-label {{
                        font-size: 13px;
                        color: #666;
                    }}
                    .vpa-total-value {{
                        font-size: 18px;
                        color: <t t-out="primary_color"/>;
                        font-weight: 600;
                    }}
                    /* Notes Section */
                    .vpa-notes-section {{
                        background: #f9f9f9;
                        border: 1px solid #e0e0e0;
                        border-radius: 5px;
                        padding: 10px;
                        margin: 10px 0;
                        page-break-inside: avoid;
                    }}
                    .vpa-notes-title {{
                        color: <t t-out="primary_color"/>;
                        margin: 0 0 6px 0;
                        font-size: 11px;
                        font-weight: 600;
                    }}
                    .vpa-notes-content {{
                        min-height: 40px;
                        background: white;
                        border: 1px solid #e0e0e0;
                        border-radius: 3px;
                        padding: 8px;
                    }}
                    .vpa-notes-content div {{
                        margin-left: 10px;
                        margin-top: 2px;
                        padding-bottom: 2px;
                        font-size: 10px;
                        color: #666;
                    }}
                    .vpa-mo-name {{
                        color: <t t-out="primary_color"/>;
                        font-weight: 600;
                    }}
                </style>

                <div class="vpa-sale-production">
                    <!-- Table Card with Items -->
                    <div class="vpa-table-card">
                        <div class="vpa-section-header">ITEMS SUMMARY DETAILS</div>
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 5%%; text-align: center;">NO.</th>
                                    <th style="width: 50%%;">PRODUCT DESCRIPTION</th>
                                    <th style="width: 12%%; text-align: center;">QUANTITY</th>
                                    <th style="width: 10%%; text-align: center;">UNIT</th>
                                    <th style="width: 23%%; text-align: center;">MO REFERENCE</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-set="line_num" t-value="0"/>
                                <t t-set="total_qty" t-value="0"/>

                                <t t-foreach="doc.order_line" t-as="line">
                                    <!-- Section Headers -->
                                    <t t-if="line.display_type == 'line_section'">
                                        <tr class="vpa-section-row">
                                            <td colspan="5"><t t-out="line.name"/></td>
                                        </tr>
                                    </t>
                                    <!-- Note Lines -->
                                    <t t-elif="line.display_type == 'line_note'">
                                        <tr class="vpa-note-row">
                                            <td colspan="5"><t t-out="line.name"/></td>
                                        </tr>
                                    </t>
                                    <!-- Regular Product Lines -->
                                    <t t-elif="line.product_uom_qty > 0">
                                        <t t-set="line_num" t-value="line_num + 1"/>
                                        <t t-set="total_qty" t-value="total_qty + line.product_uom_qty"/>
                                        <tr>
                                            <td style="text-align: center; color: #666; font-size: 10pt;"><t t-out="line_num"/></td>
                                            <td>
                                                <div style="font-weight: 500; color: #333; font-size: 10pt;">
                                                    <t t-if="line.product_id.default_code">
                                                        <span class="vpa-product-code">[<t t-out="line.product_id.default_code"/>]</span>
                                                    </t>
                                                    <t t-out="line.name"/>
                                                </div>
                                            </td>
                                            <td style="text-align: center; font-size: 10pt;">
                                                <span class="vpa-qty-badge"><t t-out="int(line.product_uom_qty) if line.product_uom_qty == int(line.product_uom_qty) else round(line.product_uom_qty, 2)"/></span>
                                            </td>
                                            <td style="text-align: center; color: #666; font-size: 10pt;">
                                                <t t-out="line.product_uom_id.name"/>
                                            </td>
                                            <td style="text-align: center;">
                                                <t t-set="mos" t-value="line.move_ids.mapped('created_production_id') if line.move_ids else []"/>
                                                <t t-if="mos">
                                                    <t t-foreach="mos" t-as="mo">
                                                        <span class="vpa-mo-badge"><t t-out="mo.name"/></span>
                                                    </t>
                                                </t>
                                                <t t-else="">
                                                    <span class="vpa-mo-pending">Pending</span>
                                                </t>
                                            </td>
                                        </tr>
                                    </t>
                                </t>
                            </tbody>
                        </table>
                    </div>

                    <!-- Total Card -->
                    <div class="vpa-total-card">
                        <table style="width: 100%%;">
                            <tr>
                                <td style="width: 70%%; text-align: right; padding-right: 15px;">
                                    <span class="vpa-total-label">Total Production Quantity:</span>
                                </td>
                                <td style="width: 30%%; text-align: center;">
                                    <span class="vpa-total-value"><t t-out="total_qty"/></span>
                                </td>
                            </tr>
                        </table>
                    </div>

                    <!-- Terms and Conditions (if exists) -->
                    <t t-if="doc.note">
                        <div class="vpa-notes-section">
                            <div class="vpa-notes-title">TERMS AND CONDITIONS:</div>
                            <div style="font-size: 10px; color: #444; line-height: 1.4;">
                                <t t-out="doc.note"/>
                            </div>
                        </div>
                    </t>

                    <!-- Production Notes -->
                    <div class="vpa-notes-section">
                        <div class="vpa-notes-title">PRODUCTION NOTES:</div>
                        <div class="vpa-notes-content">
                            <t t-set="all_mos" t-value="doc.order_line.mapped('move_ids').mapped('created_production_id')"/>
                            <t t-if="all_mos">
                                <div style="font-size: 8px; color: #666; margin-left: 0 !important;">
                                    <strong>Manufacturing Orders:</strong>
                                </div>
                                <t t-foreach="all_mos" t-as="mo">
                                    <div>
                                        • <span class="vpa-mo-name"><t t-out="mo.name"/></span> -
                                        <t t-out="mo.product_id.name"/>
                                        (<t t-out="mo.product_qty"/> <t t-out="mo.product_uom_id.name"/>)
                                        <t t-if="doc.client_order_ref">
                                            | <t t-out="doc.client_order_ref"/>
                                        </t>
                                    </div>
                                </t>
                                <div style="min-height: 20px; margin-top: 8px; border-top: 1px dotted #ddd; padding-top: 5px;">
                                    <!-- Space for additional manual notes -->
                                </div>
                            </t>
                            <t t-else="">
                                <span style="color: #bbb; font-size: 9px; font-style: italic;">No manufacturing orders created yet</span>
                            </t>
                        </div>
                    </div>
                </div>
            </t>
        </t>
    </t>
</t>'''.format(template_id=self.id)
        elif self.document_type == 'quotation_pictures':
            # Quotation with Pictures - Shows product images alongside descriptions
            main_template_arch = '''<t t-name="vpa_document_layout.report_template_{template_id}">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="doc">
            <t t-set="doc" t-value="doc.with_context(lang=doc.partner_id.lang, vpa_template_id={template_id})" />
            <t t-set="vpa_template" t-value="env['vpa.document.template'].browse({template_id})"/>
            <t t-set="primary_color" t-value="vpa_template.primary_accent_color or '#DC143C'"/>
            <t t-set="report_title" t-value="vpa_template.report_title or 'Quotation'"/>
            <t t-set="address">
                <div t-att-style="'font-family: Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 6px; color: ' + (vpa_template.primary_accent_color or '#DC143C')">CUSTOMER DETAILS</div>
                <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                    <div><strong><span t-field="doc.partner_id.name"/></strong></div>
                    <div t-field="doc.partner_id" t-options='{{"widget": "contact", "fields": ["address"], "no_marker": True}}'/>
                </div>
            </t>
            <t t-set="information_block">
                <div t-att-style="'font-family: Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 6px; color: ' + (vpa_template.primary_accent_color or '#DC143C')">ORDER INFO</div>
                <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                    <div t-if="doc.date_order">
                        <strong>Quotation Date:</strong>
                        <span t-field="doc.date_order" t-options='{{"widget": "date"}}'/>
                    </div>
                    <div t-if="doc.validity_date" style="margin-top: 4px;">
                        <strong>Expiration:</strong>
                        <span t-field="doc.validity_date" t-options='{{"widget": "date"}}'/>
                    </div>
                    <div t-if="doc.client_order_ref" style="margin-top: 4px;">
                        <strong>Customer Reference:</strong>
                        <span t-field="doc.client_order_ref"/>
                    </div>
                    <div t-if="doc.user_id" style="margin-top: 4px;">
                        <strong>Salesperson:</strong>
                        <span t-field="doc.user_id.name"/>
                    </div>
                </div>
            </t>
            <t t-set="layout_document_title">
                <t t-out="report_title"/> # <span t-field="doc.name"/>
            </t>
            <t t-call="vpa_document_layout.external_layout_vpa_template_{template_id}">
                <!-- Inline Styles for Quotation Pictures -->
                <style>
                    .vpa-quote-pictures {{
                        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                        font-size: 12px;
                        color: #333;
                    }}
                    /* Table Card Container - Match UD Quote/Order style */
                    .vpa-table-card {{
                        background: linear-gradient(135deg, #fffafa 0%%, white 100%%);
                        border-left: 3px solid <t t-out="primary_color"/>;
                        border-radius: 5px;
                        padding: 6px;
                        margin-bottom: 10px;
                        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
                    }}
                    .vpa-section-header {{
                        color: <t t-out="primary_color"/>;
                        font-size: 11px;
                        font-weight: 600;
                        text-transform: uppercase;
                        letter-spacing: 0.4px;
                        margin: 6px 6px 4px 6px;
                        padding-bottom: 3px;
                        border-bottom: 1px solid #f0f0f0;
                    }}
                    .vpa-table-card table {{
                        width: 100%%;
                        border-collapse: collapse;
                        border: none !important;
                    }}
                    .vpa-table-card th {{
                        background: transparent;
                        color: <t t-out="primary_color"/>;
                        font-weight: 600;
                        text-transform: uppercase;
                        font-size: 10px;
                        padding: 5px 4px;
                        border: none !important;
                        border-bottom: 1px solid #f0f0f0 !important;
                        border-right: 1px solid #f0f0f0 !important;
                        letter-spacing: 0.3px;
                    }}
                    .vpa-table-card th:last-child {{
                        border-right: none !important;
                    }}
                    .vpa-table-card td {{
                        padding: 4px 4px;
                        font-size: 11px;
                        color: #333;
                        border: none !important;
                        border-bottom: 1px solid #f8f8f8 !important;
                        border-right: 1px solid #f8f8f8 !important;
                        vertical-align: top;
                        line-height: 1.3;
                    }}
                    .vpa-table-card td:last-child {{
                        border-right: none !important;
                    }}
                    .vpa-table-card tbody tr:last-child td {{
                        border-bottom: none !important;
                    }}
                    .vpa-section-row td {{
                        background: #f0f0f0;
                        font-weight: 700;
                        padding: 6px 4px;
                        color: #666;
                        font-size: 12px;
                        border-bottom: 1px solid #ddd !important;
                    }}
                    .vpa-note-row td {{
                        padding: 4px 12px;
                        font-style: italic;
                        color: #555;
                        font-size: 11px;
                        background: #fafafa;
                        border-bottom: 1px solid #f0f0f0 !important;
                    }}
                    .vpa-product-image {{
                        max-width: 80px;
                        max-height: 80px;
                        width: auto;
                        height: auto;
                        object-fit: contain;
                        border-radius: 4px;
                    }}
                    .vpa-product-title {{
                        font-weight: 600;
                        color: #333;
                        font-size: 10pt;
                    }}
                    .vpa-product-code {{
                        color: #777;
                        font-size: 10px;
                    }}
                    .vpa-product-details {{
                        font-size: 9pt;
                        color: #555;
                        line-height: 1.5;
                        margin-top: 5px;
                    }}
                    .vpa-qty-badge {{
                        display: inline-block;
                        background: white;
                        color: <t t-out="primary_color"/>;
                        padding: 2px 6px;
                        border-radius: 2px;
                        font-weight: 600;
                        font-size: 11px;
                        border: 1px solid <t t-out="primary_color"/>;
                    }}
                    .vpa-amount-badge {{
                        display: inline-block;
                        background: <t t-out="primary_color"/>;
                        color: white;
                        padding: 2px 8px;
                        border-radius: 2px;
                        font-weight: 600;
                        font-size: 11px;
                    }}
                    .vpa-total-card {{
                        background: linear-gradient(135deg, #fffafa 0%%, white 100%%);
                        border-left: 3px solid <t t-out="primary_color"/>;
                        padding: 10px;
                        border-radius: 5px;
                        margin: 10px 0;
                        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
                    }}
                    .vpa-total-card table {{
                        width: 100%%;
                        border-collapse: collapse;
                    }}
                    .vpa-total-card td {{
                        padding: 6px 8px;
                        font-size: 11px;
                        border: none !important;
                    }}
                    .vpa-total-label {{
                        font-size: 11px;
                        color: #666;
                    }}
                    .vpa-total-value {{
                        font-size: 11px;
                        color: #333;
                        font-weight: 500;
                    }}
                    .vpa-grand-total-label {{
                        font-size: 14px;
                        color: <t t-out="primary_color"/>;
                        font-weight: 600;
                    }}
                    .vpa-grand-total-value {{
                        font-size: 18px;
                        color: <t t-out="primary_color"/>;
                        font-weight: 600;
                    }}
                    .vpa-notes-section {{
                        background: #f9f9f9;
                        border: 1px solid #e0e0e0;
                        border-radius: 5px;
                        padding: 10px;
                        margin: 10px 0;
                        page-break-inside: avoid;
                    }}
                    .vpa-notes-title {{
                        color: <t t-out="primary_color"/>;
                        margin: 0 0 6px 0;
                        font-size: 11px;
                        font-weight: 600;
                    }}
                </style>

                <div class="vpa-quote-pictures">
                    <!-- Order Lines Table with Pictures -->
                    <t t-set="display_discount" t-value="any(line.discount for line in doc.order_line)"/>
                    <t t-set="lines_to_report" t-value="doc._get_order_lines_to_report()"/>

                    <div class="vpa-table-card">
                        <div class="vpa-section-header">ORDER DETAILS</div>
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 5%%; text-align: center;">NO.</th>
                                    <th style="width: 45%%;">DESCRIPTION</th>
                                    <th style="width: 8%%; text-align: center;">QTY</th>
                                    <th style="width: 8%%; text-align: center;">UNIT</th>
                                    <th style="width: 14%%; text-align: right;">UNIT PRICE</th>
                                    <th t-if="display_discount" style="width: 6%%; text-align: center;">DISC.</th>
                                    <th style="width: 14%%; text-align: right;">AMOUNT</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-set="line_num" t-value="0"/>
                                <t t-foreach="lines_to_report" t-as="line">
                                    <!-- Section Headers -->
                                    <t t-if="line.display_type == 'line_section'">
                                        <tr class="vpa-section-row">
                                            <td t-att-colspan="'7' if display_discount else '6'"><span t-field="line.name"/></td>
                                        </tr>
                                    </t>
                                    <!-- Note Lines -->
                                    <t t-elif="line.display_type == 'line_note'">
                                        <tr class="vpa-note-row">
                                            <td t-att-colspan="'7' if display_discount else '6'"><span t-field="line.name"/></td>
                                        </tr>
                                    </t>
                                    <!-- Regular Product Lines with Pictures -->
                                    <t t-else="">
                                        <t t-set="line_num" t-value="line_num + 1"/>
                                        <t t-set="product_name_parts" t-value="(line.name or '').split('\\n', 1)"/>
                                        <t t-set="product_title" t-value="product_name_parts[0] if product_name_parts else ''"/>
                                        <t t-set="product_details" t-value="product_name_parts[1] if len(product_name_parts) > 1 else ''"/>
                                        <tr>
                                            <!-- Line Number -->
                                            <td style="text-align: center; vertical-align: top; padding-top: 12px;">
                                                <t t-out="line_num"/>
                                            </td>
                                            <!-- Description with Image -->
                                            <td>
                                                <!-- Product Title Row -->
                                                <div class="vpa-product-title">
                                                    <t t-if="line.product_id.default_code">
                                                        <span class="vpa-product-code">[<t t-out="line.product_id.default_code"/>]</span>
                                                    </t>
                                                    <t t-out="product_title"/>
                                                </div>
                                                <!-- Image + Details Row -->
                                                <div style="display: table; width: 100%%; margin-top: 8px;">
                                                    <div style="display: table-cell; width: 90px; vertical-align: top;">
                                                        <t t-if="line.product_id.image_512">
                                                            <img t-att-src="image_data_uri(line.product_id.image_512)"
                                                                 class="vpa-product-image"
                                                                 style="max-width: 80px; max-height: 80px; width: auto; height: auto;"
                                                                 alt="Product"/>
                                                        </t>
                                                    </div>
                                                    <div style="display: table-cell; vertical-align: top; padding-left: 10px;">
                                                        <t t-if="product_details">
                                                            <div class="vpa-product-details">
                                                                <t t-out="product_details.replace('\\n', '&lt;br/&gt;')"/>
                                                            </div>
                                                        </t>
                                                    </div>
                                                </div>
                                            </td>
                                            <!-- Quantity -->
                                            <td style="text-align: center; vertical-align: top; padding-top: 12px;">
                                                <span class="vpa-qty-badge"><t t-out="int(line.product_uom_qty) if line.product_uom_qty == int(line.product_uom_qty) else round(line.product_uom_qty, 2)"/></span>
                                            </td>
                                            <!-- Unit -->
                                            <td style="text-align: center; vertical-align: top; padding-top: 12px;">
                                                <span t-field="line.product_uom_id"/>
                                            </td>
                                            <!-- Unit Price -->
                                            <td style="text-align: right; vertical-align: top; padding-top: 12px;">
                                                <t t-out="'{{:,.2f}}'.format(line.price_unit)"/>
                                            </td>
                                            <!-- Discount -->
                                            <td t-if="display_discount" style="text-align: center; vertical-align: top; padding-top: 12px;">
                                                <span t-field="line.discount"/><t t-out="'%%'"/>
                                            </td>
                                            <!-- Amount -->
                                            <td style="text-align: right; vertical-align: top; padding-top: 12px;">
                                                <span class="vpa-amount-badge"><span t-field="line.price_subtotal"/></span>
                                            </td>
                                        </tr>
                                    </t>
                                </t>
                            </tbody>
                        </table>
                    </div>

                    <!-- Totals Card -->
                    <div style="overflow: hidden;">
                        <div class="vpa-total-card" style="width: 350px; float: right;">
                            <table style="width: 100%%;">
                                <tr>
                                    <td style="text-align: right; width: 60%%;">
                                        <span class="vpa-total-label">Subtotal:</span>
                                    </td>
                                    <td style="text-align: right; width: 40%%;">
                                        <span class="vpa-total-value"><span t-field="doc.amount_untaxed"/></span>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="text-align: right;">
                                        <span class="vpa-total-label">Taxes:</span>
                                    </td>
                                    <td style="text-align: right;">
                                        <span class="vpa-total-value"><span t-field="doc.amount_tax"/></span>
                                    </td>
                                </tr>
                                <tr style="border-top: 1px solid #ddd;">
                                    <td style="text-align: right; padding-top: 8px;">
                                        <span class="vpa-grand-total-label">Total:</span>
                                    </td>
                                    <td style="text-align: right; padding-top: 8px;">
                                        <span class="vpa-grand-total-value"><span t-field="doc.amount_total"/></span>
                                    </td>
                                </tr>
                            </table>
                        </div>
                    </div>

                    <!-- Terms and Conditions -->
                    <t t-if="doc.note">
                        <div class="vpa-notes-section" style="clear: both;">
                            <div class="vpa-notes-title">TERMS AND CONDITIONS:</div>
                            <div style="font-size: 10px; color: #444; line-height: 1.4;">
                                <t t-out="doc.note"/>
                            </div>
                        </div>
                    </t>
                </div>
            </t>
        </t>
    </t>
</t>'''.format(template_id=self.id)
        else:
            # For other document types, create a template with standard VPA styling
            main_template_arch = '''<t t-name="vpa_document_layout.report_template_{template_id}">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="doc">
            <t t-set="vpa_template" t-value="env['vpa.document.template'].browse({template_id})"/>
            <t t-set="address">
                <t t-if="doc.partner_id">
                    <div t-att-style="'font-family: Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 6px; color: ' + (vpa_template.primary_accent_color or '#DC143C')">CUSTOMER DETAILS</div>
                    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                        <div><strong><span t-field="doc.partner_id.name"/></strong></div>
                        <div t-field="doc.partner_id" t-options='{{"widget": "contact", "fields": ["address"], "no_marker": True}}'/>
                    </div>
                </t>
            </t>
            <t t-set="information_block">
                <div t-att-style="'font-family: Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 6px; color: ' + (vpa_template.primary_accent_color or '#DC143C')">DOCUMENT INFO</div>
                <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                    <div t-if="doc.name">
                        <strong>Reference:</strong>
                        <span t-field="doc.name"/>
                    </div>
                </div>
            </t>
            <t t-set="layout_document_title">
                {doc_type_title} # <span t-field="doc.name"/>
            </t>
            <t t-call="vpa_document_layout.external_layout_vpa_template_{template_id}">
                <div class="page" style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                    <p>VPA Template for {doc_type} (Document content pending)</p>
                </div>
            </t>
        </t>
    </t>
</t>'''.format(template_id=self.id, doc_type=self.document_type, doc_type_title=self.document_type.replace('_', ' ').title())

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

    <div t-attf-class="article o_report_layout_vpa o_company_#{company.id}_layout" style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">

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
                /* height removed to allow natural content flow - footer is handled by wkhtmltopdf */
                padding: 0 !important;
                margin: 0 !important;
                box-sizing: border-box;
                background: white !important;
            }
            .o_report_layout_vpa .page-layout-table {
                width: 100%%;
                /* height removed to allow natural content flow */
                border-collapse: collapse;
                border-spacing: 0;
                border: none !important;
            }
            .o_report_layout_vpa .page-layout-table td.content-cell {
                /* height removed to allow natural content flow */
                vertical-align: top;
                padding: 18px;
                border: none !important;
            }
            .o_report_layout_vpa .page-layout-table tr {
                border: none !important;
            }
            /* Main product table - ensure visibility in PDF */
            /* Target ALL tables including Odoo's table.table class */
            .o_report_layout_vpa table.table,
            .o_report_layout_vpa table.o_main_table,
            table.table,
            table.o_main_table {
                border-collapse: collapse !important;
                border-spacing: 0 !important;
                width: 100%% !important;
                border: 2px solid %s !important;
                margin-bottom: 20px !important;
            }
            .o_report_layout_vpa table.table thead th,
            .o_report_layout_vpa table.o_main_table thead th,
            table.table thead th,
            table.o_main_table thead th {
                background: %s !important;
                color: %s !important;
                padding: 14px 12px !important;
                font-weight: bold !important;
                font-size: 15pt !important;
                border: 1px solid %s !important;
                text-align: left !important;
                %s
            }
            .o_report_layout_vpa table.table tbody td,
            .o_report_layout_vpa table.o_main_table tbody td,
            table.table tbody td,
            table.o_main_table tbody td {
                padding: 12px 12px !important;
                border: 1px solid %s !important;
                vertical-align: top !important;
                font-size: 14pt !important;
                line-height: 1.5 !important;
            }
            .o_report_layout_vpa table.table tbody tr:nth-child(even),
            .o_report_layout_vpa table.o_main_table tbody tr:nth-child(even),
            table.table tbody tr:nth-child(even),
            table.o_main_table tbody tr:nth-child(even) {
                background-color: %s !important;
            }
            .o_report_layout_vpa table.table tbody tr:nth-child(odd),
            .o_report_layout_vpa table.o_main_table tbody tr:nth-child(odd),
            table.table tbody tr:nth-child(odd),
            table.o_main_table tbody tr:nth-child(odd) {
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
                padding: 12px 14px !important;
                border: 1px solid #dee2e6 !important;
                font-size: 14pt !important;
            }
            .o_report_layout_vpa table.o_total_table tr {
                border-bottom: 1px solid #dee2e6 !important;
            }
            .o_report_layout_vpa table.o_total_table tr:last-child {
                border-top: 2px solid #000 !important;
                background-color: #f8f9fa !important;
                font-weight: bold !important;
                font-size: 16pt !important;
            }
            .o_report_layout_vpa table.o_total_table tr:last-child td {
                font-weight: bold !important;
            }
            .o_report_layout_vpa .o_price_total {
                font-weight: bold !important;
                font-size: 18pt !important;
            }
        </style>

        <!-- Page Content Wrapper -->
        <div class="page">
            <!-- Decorative circle - only shown in body if header_repeat_on_pages is False -->
            <!-- When header_repeat_on_pages is True, circle comes from wkhtmltopdf header URL -->
            <t t-if="not vpa_template.header_repeat_on_pages">
                <svg t-if="%s" style="position: fixed; top: 0; right: 0; z-index: -1;" width="%s" height="%s" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="%s" cy="%s" r="%s" fill="%s" fill-opacity="%s"/>
                </svg>
            </t>

            <!-- Real HTML table for reliable footer positioning in PDF -->
            <table class="page-layout-table">
                <tr>
                    <td class="content-cell">
            <!-- Header (only shown in body if header_repeat_on_pages is False) -->
            <!-- When header_repeat_on_pages is True, header comes from wkhtmltopdf header URL -->
        <t t-if="not vpa_template.header_repeat_on_pages">
        <div t-attf-style="position: relative; z-index: 1; padding-bottom: 15px; margin-bottom: 25px; border-bottom: 1px solid %s;">
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
        </t>

        <!-- Document Title - Full Width Right Aligned, vertically centered between lines -->
        <div t-if="layout_document_title" style="margin-bottom: 20px;">
            <h2 t-attf-style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 28pt; font-weight: bold; color: %s; margin: 15px 0; text-align: right;" t-out="layout_document_title"/>
            <div t-attf-style="border-bottom: 1px solid %s;"></div>
        </div>

        <!-- Customer Details and Order Info (Two columns below title) -->
        <table t-if="address or information_block" style="width: 100%%; margin-bottom: 25px; border-collapse: collapse;">
            <tbody>
                <tr>
                    <td t-if="address" style="width: 50%%; vertical-align: top; padding-right: 20px;">
                        <div style="font-size: 10pt; line-height: 1.8; color: #555;">
                            <t t-out="address"/>
                        </div>
                    </td>
                    <td t-if="information_block" style="width: 50%%; vertical-align: top; text-align: right; padding-left: 20px;">
                        <div style="font-size: 9pt; line-height: 1.8; color: #555; text-align: right;">
                            <t t-out="information_block"/>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>

            <!-- Document content -->
            <t t-out="0"/>
                    </td><!-- Close content-cell -->
                </tr>
            </table><!-- Close page-layout-table -->
        </div><!-- Close page -->
    </div><!-- Close article -->
</t>'''

        # NOTE: Footer is rendered via wkhtmltopdf --footer-html parameter
        # NOT inline in the template (to avoid duplication)

        # Get table styles
        table_styles = self._get_table_styles()

        # Finalize arch_content with all parameters (30 total - page_height removed)
        arch_content = arch_content % (
            self.id,
            self.id,
            self.primary_accent_color,
            self.secondary_accent_color,
            page_size_css,  # @page size
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
            self.primary_accent_color,  # Document title separator line color (now primary)
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
            'sale_production': 'sale.order',
            'quotation_pictures': 'sale.order',
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

    @api.model
    def _cleanup_and_regenerate_templates(self):
        """
        Called from data/regenerate_templates.xml on EVERY module upgrade.
        1. Cleanup orphan report actions (fixes duplicate Print menu items)
        2. Regenerate sale_production templates (fixes QWeb syntax issues)
        """
        _logger.info("VPA Document Layout: Running upgrade cleanup and regeneration...")

        # STEP 1: Cleanup orphan report actions that cause duplicate Print menu items
        try:
            orphan_reports = self.env['ir.actions.report'].search([
                ('report_name', 'like', 'vpa_document_layout.report_template_%')
            ])
            template_report_ids = self.search([]).mapped('report_action_id').ids

            orphan_count = 0
            for report in orphan_reports:
                if report.id not in template_report_ids:
                    _logger.info(f"Deleting orphan report: {report.name} (ID: {report.id})")
                    report.unlink()
                    orphan_count += 1

            if orphan_count:
                _logger.info(f"VPA Document Layout: Removed {orphan_count} orphan report action(s)")
        except Exception as e:
            _logger.warning(f"VPA Document Layout: Could not cleanup orphan reports: {e}")

        # STEP 2: Regenerate sale_production templates to fix QWeb syntax issues
        try:
            production_templates = self.search([
                ('document_type', '=', 'sale_production')
            ])
            for template in production_templates:
                _logger.info(f"Regenerating template: {template.name} (ID: {template.id})")
                # Delete existing QWeb views for this template
                existing_views = self.env['ir.ui.view'].search([
                    '|', '|',
                    ('key', 'like', f'%template_{template.id}%'),
                    ('key', 'like', f'%inherit_{template.id}%'),
                    ('name', 'like', f'%{template.id}')
                ])
                if existing_views:
                    _logger.info(f"Deleting {len(existing_views)} existing views for template {template.id}")
                    existing_views.unlink()
                # Recreate the QWeb template with fixed syntax
                template._create_qweb_template()
            _logger.info(f"VPA Document Layout: Regenerated {len(production_templates)} sale_production template(s)")
        except Exception as e:
            _logger.warning(f"VPA Document Layout: Could not regenerate templates: {e}")

        return True
