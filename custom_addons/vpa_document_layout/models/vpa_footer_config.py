# -*- coding: utf-8 -*-
from odoo import models, fields, api
from markupsafe import Markup


class VPAFooterConfig(models.Model):
    _name = 'vpa.footer.config'
    _description = 'VPA Header & Footer Configuration'
    _order = 'sequence, name'

    name = fields.Char(string='Configuration Name', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        required=True, default=lambda self: self.env.company,
        ondelete='cascade'
    )
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    # Footer Type
    footer_type = fields.Selection([
        ('customer', 'Customer-Facing (Quotes, Invoices, PO, Delivery)'),
        ('internal', 'Internal Documents (MFG, Picking, Internal Transfers)'),
        ('custom', 'Custom'),
    ], string='Footer Type', required=True, default='customer')

    # Set as Default
    is_default_customer = fields.Boolean(
        string='Default for Customer Documents',
        help='Use this config as default for customer-facing documents (Quotes, Invoices, etc.)'
    )
    is_default_internal = fields.Boolean(
        string='Default for Internal Documents',
        help='Use this config as default for internal documents (Manufacturing, Picking, etc.)'
    )

    # ==================== HEADER SECTION ====================
    show_header = fields.Boolean(string='Enable Header', default=True)
    header_show_logo = fields.Boolean(string='Show Company Logo', default=True)
    header_show_company_name = fields.Boolean(string='Show Company Name', default=True)
    header_show_company_details = fields.Boolean(
        string='Show Company Details',
        default=False,
        help='Show company address, phone, email in header'
    )
    header_show_document_title = fields.Boolean(
        string='Show Document Title',
        default=True,
        help='Show document type (e.g., "Production Order", "Invoice")'
    )
    header_custom_title = fields.Char(
        string='Custom Title',
        help='Override the default document title'
    )
    header_show_date = fields.Boolean(string='Show Date', default=True)
    header_date_format = fields.Selection([
        ('short', 'Short (12/16/2025)'),
        ('medium', 'Medium (Dec 16, 2025)'),
        ('long', 'Long (December 16, 2025)'),
    ], string='Date Format', default='medium')
    header_layout = fields.Selection([
        ('standard', 'Standard (Logo left, details right)'),
        ('centered', 'Centered (Logo and company name centered)'),
        ('minimal', 'Minimal (Company name only)'),
        ('custom_html', 'Custom HTML'),
    ], string='Header Layout', default='standard')
    header_custom_html = fields.Html(
        string='Custom Header HTML',
        help='Use placeholders: {{company_name}}, {{company_logo}}, {{document_title}}, {{date}}'
    )
    header_background_color = fields.Char(string='Header Background', default='#ffffff')
    header_text_color = fields.Char(string='Header Text Color', default='#333333')
    header_border_bottom = fields.Boolean(string='Show Bottom Border', default=True)
    header_border_color = fields.Char(string='Header Border Color', default='#dee2e6')
    header_height = fields.Char(string='Header Height', default='25mm', help='Height reserved for header (e.g., 25mm, 1in)')

    # ==================== FOOTER SECTION ====================
    footer_height = fields.Char(string='Footer Height', default='30mm', help='Height reserved for footer (e.g., 30mm, 1in). Reduce to minimize gap between content and footer.')
    # Footer Layout
    footer_layout = fields.Selection([
        ('single', 'Single Column (Centered)'),
        ('two_col', 'Two Columns'),
        ('three_col', 'Three Columns'),
        ('custom_html', 'Custom HTML'),
    ], string='Layout', default='single')

    # Styling
    show_border = fields.Boolean(string='Show Top Border', default=True)
    border_color = fields.Char(string='Border Color', default='#dee2e6')
    show_shape = fields.Boolean(string='Show Decorative Shape', default=False)
    shape_color = fields.Char(string='Shape Color', default='#21b799')
    shape_opacity = fields.Float(string='Shape Opacity', default=0.1)
    text_color = fields.Char(string='Text Color', default='#666666')
    font_size = fields.Char(string='Font Size', default='8pt')

    # Page Number Styling
    page_number_style = fields.Selection([
        ('plain', 'Plain Text'),
        ('badge', 'Colored Badge'),
    ], string='Page Number Style', default='badge', help='Style for page numbers in footer')
    page_number_bg_color = fields.Char(
        string='Page Number Background',
        default='#875a7b',
        help='Background color for page number badge (used when style is Badge)'
    )

    # Content Options
    show_bank_details = fields.Boolean(string='Show Bank Details', default=True)
    show_page_numbers = fields.Boolean(string='Show Page Numbers', default=True)
    show_company_footer = fields.Boolean(
        string='Show Company Footer Text',
        default=True,
        help='Show the footer text configured in Settings > Companies > Report Footer'
    )
    computer_generated_note = fields.Char(
        string='Computer Generated Note',
        default='This is a computer generated document',
        help='Note displayed on internal documents'
    )

    # Column Content (for multi-column layouts)
    column_1_title = fields.Char(string='Column 1 Title')
    column_1_content = fields.Html(string='Column 1 Content')
    column_2_title = fields.Char(string='Column 2 Title')
    column_2_content = fields.Html(string='Column 2 Content')
    column_3_title = fields.Char(string='Column 3 Title')
    column_3_content = fields.Html(string='Column 3 Content')

    # Custom HTML (for full control)
    custom_html = fields.Html(
        string='Custom Footer HTML',
        help='Use placeholders: {{company_name}}, {{bank_name}}, {{bank_account}}, {{bank_bic}}, {{company_footer}}'
    )

    # Preview
    preview = fields.Html(compute='_compute_preview', sanitize=False)

    @api.model
    def get_footer_for_report(self, company_id, report_xml_id=None):
        """Get appropriate footer config based on report type"""
        # Determine if customer-facing or internal
        customer_reports = [
            'sale.report_saleorder',
            'sale.action_report_saleorder',
            'account.account_invoices',
            'account.report_invoice',
            'purchase.report_purchaseorder',
            'purchase.action_report_purchase_order',
            'stock.report_deliveryslip',
            'stock.report_delivery_document',
        ]
        internal_reports = [
            'mrp.report_mrporder',
            'mrp.action_report_production_order',
            'mrp.report_workorder',
            'stock.report_picking',
            'stock.action_report_picking',
            'stock.report_reception',
            # VPA Internal Transfer
            'vpa_acc_int_transfer.report_internal_transfer',
            'vpa_acc_int_transfer.action_report_internal_transfer',
        ]

        report_xml_id = report_xml_id or ''

        if any(r in report_xml_id for r in customer_reports):
            footer_type = 'customer'
        elif any(r in report_xml_id for r in internal_reports):
            footer_type = 'internal'
        else:
            footer_type = 'customer'  # Default to customer

        # Find default footer for this type
        if footer_type == 'customer':
            footer = self.search([
                ('company_id', '=', company_id),
                ('is_default_customer', '=', True),
                ('active', '=', True)
            ], limit=1)
        else:
            footer = self.search([
                ('company_id', '=', company_id),
                ('is_default_internal', '=', True),
                ('active', '=', True)
            ], limit=1)

        # Fallback to any default if specific type not found
        if not footer:
            footer = self.search([
                ('company_id', '=', company_id),
                ('active', '=', True)
            ], limit=1)

        return footer or self.browse()

    def _render_custom_html(self, company):
        """Render custom HTML with placeholder substitution"""
        self.ensure_one()

        html = self.custom_html or ''

        # Get bank info
        bank = company.partner_id.bank_ids[:1] if company.partner_id.bank_ids else False

        # Replace placeholders
        replacements = {
            '{{company_name}}': company.name or '',
            '{{company_footer}}': company.report_footer or '',
            '{{bank_name}}': bank.bank_id.name if bank and bank.bank_id else '',
            '{{bank_account}}': bank.acc_number if bank else '',
            '{{bank_bic}}': bank.bank_bic if bank else '',
        }

        for placeholder, value in replacements.items():
            html = html.replace(placeholder, str(value))

        return Markup(html)

    @api.depends('name', 'footer_type', 'footer_layout', 'show_bank_details',
                 'show_page_numbers', 'page_number_style', 'page_number_bg_color',
                 'computer_generated_note', 'show_border',
                 'border_color', 'text_color', 'column_1_content', 'column_2_content',
                 'column_3_content', 'custom_html')
    def _compute_preview(self):
        """Generate footer preview"""
        for record in self:
            if not record.company_id:
                record.preview = '<div style="text-align:center;color:#999;">Select a company to see preview</div>'
                continue

            company = record.company_id
            border_style = f"border-top: 1px solid {record.border_color};" if record.show_border else ""

            preview_html = f'''
            <div style="font-family: Arial, sans-serif; font-size: {record.font_size};
                        color: {record.text_color}; {border_style} padding: 10px;
                        background: #f9f9f9; margin-top: 10px;">
            '''

            if record.footer_layout == 'single':
                preview_html += '<div style="text-align: center;">'

                if record.footer_type == 'internal' and record.computer_generated_note:
                    preview_html += f'<div style="font-style: italic; margin-bottom: 5px;">{record.computer_generated_note}</div>'

                if record.show_bank_details and company.partner_id.bank_ids:
                    bank = company.partner_id.bank_ids[0]
                    bank_name = bank.bank_id.name if bank.bank_id else 'Bank'
                    preview_html += f'<div><strong>Bank:</strong> {bank_name} | Account: {bank.acc_number or "N/A"}</div>'

                if record.show_company_footer and company.report_footer:
                    preview_html += f'<div>{company.report_footer}</div>'

                if record.show_page_numbers:
                    if record.page_number_style == 'badge':
                        bg_color = record.page_number_bg_color or '#875a7b'
                        preview_html += f'<div style="text-align: right; margin-top: 12px;"><span style="background-color: {bg_color}; color: #fff; padding: 4px 12px; border-radius: 3px; font-size: 8pt;">Page 1 of 1</span></div>'
                    else:
                        preview_html += '<div style="text-align: right; margin-top: 12px;">Page 1 of 1</div>'

                preview_html += '</div>'

            elif record.footer_layout in ('two_col', 'three_col'):
                cols = 3 if record.footer_layout == 'three_col' else 2
                preview_html += '<table style="width: 100%; table-layout: fixed;"><tr>'

                if record.column_1_title or record.column_1_content:
                    preview_html += f'''
                    <td style="vertical-align: top; padding-right: 10px;">
                        <strong>{record.column_1_title or ''}</strong><br/>
                        {record.column_1_content or '(Column 1 content)'}
                    </td>
                    '''
                else:
                    preview_html += '<td style="vertical-align: top;">(Column 1)</td>'

                if record.column_2_title or record.column_2_content:
                    preview_html += f'''
                    <td style="vertical-align: top; padding: 0 10px;">
                        <strong>{record.column_2_title or ''}</strong><br/>
                        {record.column_2_content or '(Column 2 content)'}
                    </td>
                    '''
                else:
                    preview_html += '<td style="vertical-align: top;">(Column 2)</td>'

                if cols == 3:
                    if record.column_3_title or record.column_3_content:
                        preview_html += f'''
                        <td style="vertical-align: top; padding-left: 10px;">
                            <strong>{record.column_3_title or ''}</strong><br/>
                            {record.column_3_content or '(Column 3 content)'}
                        </td>
                        '''
                    else:
                        preview_html += '<td style="vertical-align: top;">(Column 3)</td>'

                preview_html += '</tr></table>'

                if record.show_page_numbers:
                    if record.page_number_style == 'badge':
                        bg_color = record.page_number_bg_color or '#875a7b'
                        preview_html += f'<div style="text-align: right; margin-top: 12px;"><span style="background-color: {bg_color}; color: #fff; padding: 4px 12px; border-radius: 3px; font-size: 8pt;">Page 1 of 1</span></div>'
                    else:
                        preview_html += '<div style="text-align: right; margin-top: 12px;">Page 1 of 1</div>'

            elif record.footer_layout == 'custom_html':
                if record.custom_html:
                    preview_html += f'<div>{record._render_custom_html(company)}</div>'
                else:
                    preview_html += '<div style="text-align:center;color:#999;">Enter custom HTML above</div>'

            preview_html += '</div>'
            record.preview = preview_html

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure only one default per type per company"""
        records = super().create(vals_list)
        for record in records:
            record._ensure_single_default()
        return records

    def write(self, vals):
        """Ensure only one default per type per company"""
        result = super().write(vals)
        if 'is_default_customer' in vals or 'is_default_internal' in vals:
            for record in self:
                record._ensure_single_default()
        return result

    def _ensure_single_default(self):
        """Ensure only one footer is default per type per company"""
        self.ensure_one()

        if self.is_default_customer:
            # Unset other customer defaults for same company
            others = self.search([
                ('id', '!=', self.id),
                ('company_id', '=', self.company_id.id),
                ('is_default_customer', '=', True)
            ])
            if others:
                others.write({'is_default_customer': False})

        if self.is_default_internal:
            # Unset other internal defaults for same company
            others = self.search([
                ('id', '!=', self.id),
                ('company_id', '=', self.company_id.id),
                ('is_default_internal', '=', True)
            ])
            if others:
                others.write({'is_default_internal': False})

    @api.model
    def create_default_footers_for_company(self, company):
        """Create default footer configs for a company if they don't exist"""
        # Check if company already has footers
        existing = self.search([('company_id', '=', company.id)], limit=1)
        if existing:
            return existing

        # Create Customer Footer (Single Column)
        customer_footer = self.create({
            'name': 'Customer Documents Footer',
            'company_id': company.id,
            'footer_type': 'customer',
            'is_default_customer': True,
            'footer_layout': 'single',
            'show_bank_details': True,
            'show_page_numbers': True,
            'show_company_footer': True,
            'show_border': True,
            'border_color': '#dee2e6',
            'text_color': '#666666',
            'font_size': '8pt',
            'sequence': 10,
        })

        # Create Internal Footer
        internal_footer = self.create({
            'name': 'Internal Documents Footer',
            'company_id': company.id,
            'footer_type': 'internal',
            'is_default_internal': True,
            'footer_layout': 'single',
            'show_bank_details': False,
            'show_page_numbers': True,
            'show_company_footer': False,
            'computer_generated_note': 'This is a computer generated document',
            'show_border': True,
            'border_color': '#dee2e6',
            'text_color': '#888888',
            'font_size': '8pt',
            'sequence': 20,
        })

        # Create 3-Column Customer Footer
        three_col_footer = self.create({
            'name': 'Customer Footer - 3 Column',
            'company_id': company.id,
            'footer_type': 'customer',
            'is_default_customer': False,
            'footer_layout': 'three_col',
            'show_bank_details': False,
            'show_page_numbers': True,
            'show_company_footer': False,
            'show_shape': True,
            'shape_color': '#21b799',
            'shape_opacity': 0.1,
            'show_border': False,
            'text_color': '#666666',
            'font_size': '8pt',
            'sequence': 15,
            'column_1_title': 'Company Information',
            'column_1_content': '<p style="margin: 0; line-height: 1.6;"><strong>Your Company</strong><br/>Address<br/>TIN: XXX<br/>VAT: XXX</p>',
            'column_2_title': 'Contact',
            'column_2_content': '<p style="margin: 0; line-height: 1.6;">Phone: +XXX<br/>Email: info@company.com<br/>Website: www.company.com</p>',
            'column_3_title': 'Bank Information',
            'column_3_content': '<p style="margin: 0; line-height: 1.6;">Bank: Your Bank<br/>Account: XXXX<br/>SWIFT: XXXX</p>',
        })

        return customer_footer | internal_footer | three_col_footer

    @api.model
    def init_default_footers_all_companies(self):
        """Create default footers for all companies that don't have them"""
        companies = self.env['res.company'].search([])
        for company in companies:
            self.create_default_footers_for_company(company)
