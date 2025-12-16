# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.tools.image import image_data_uri
import logging

_logger = logging.getLogger(__name__)


class VPATemplatePreview(http.Controller):

    @http.route('/vpa/template/preview/<int:template_id>', type='http', auth='user')
    def preview_template(self, template_id, **kwargs):
        """Generate HTML preview for a VPA document template with page margins"""
        template = request.env['vpa.document.template'].browse(template_id)

        if not template.exists():
            return request.not_found()

        # Render HTML preview with page border
        return request.render('vpa_document_layout.template_preview_fullpage', {
            'template': template,
        })

    @http.route('/vpa/template/preview/pdf/<int:template_id>', type='http', auth='user')
    def preview_template_pdf(self, template_id, **kwargs):
        """Download PDF preview with SAME dummy data as HTML preview"""
        template = request.env['vpa.document.template'].browse(template_id)

        if not template.exists():
            return request.not_found()

        _logger.info(f"Generating PDF preview for template ID: {template.id}, name: {template.name}")

        # Check if the external layout template exists
        external_layout_key = f'vpa_document_layout.external_layout_vpa_template_{template.id}'
        layout_view = request.env['ir.ui.view'].search([('key', '=', external_layout_key)], limit=1)
        if layout_view:
            _logger.info(f"Found external layout view {layout_view.id} with key: {external_layout_key}")
            arch_str = str(layout_view.arch or '')
            has_footer = 'footer-wave' in arch_str or 'footer-cell' in arch_str
            _logger.info(f"Layout view has footer content: {has_footer}")
            if has_footer:
                _logger.warning(f"⚠️  LAYOUT VIEW CONTAINS FOOTER! Last 300 chars: {arch_str[-300:]}")
            else:
                _logger.info(f"✅ Layout view has NO footer (correct!). Last 200 chars: {arch_str[-200:]}")
        else:
            _logger.error(f"❌ External layout view NOT FOUND: {external_layout_key}")

        try:
            # Get a sample document to render with REAL data
            sample_doc = template._get_sample_document()
            _logger.info(f"🔍 Sample doc result: {sample_doc}")

            if not sample_doc:
                # Fallback to hardcoded preview if no sample document
                html_content = request.env['ir.ui.view']._render_template(
                    'vpa_document_layout.vpa_layout_preview',
                    {
                        'template': template,
                        'company': template.company_id,
                        'config': template,
                        'image_data_uri': image_data_uri,
                    }
                )
            else:
                # Render with REAL document data (same as Real Print!)
                report_template = f'vpa_document_layout.report_template_{template.id}'
                html_content = request.env['ir.ui.view']._render_template(
                    report_template,
                    {
                        'docs': sample_doc,
                        'doc_ids': sample_doc.ids,
                        'doc_model': sample_doc._name,
                        'company': template.company_id,
                    }
                )

            # Decode if bytes
            if isinstance(html_content, bytes):
                html_str = html_content.decode('utf-8')
            else:
                html_str = str(html_content)

            _logger.info(f"HTML rendered, size: {len(html_str)} chars")

            # DEBUG: Save to file
            with open('/tmp/vpa_pdf_debug.html', 'w', encoding='utf-8') as f:
                f.write(html_str)

            # Convert to PDF with footer-html approach
            IrActionsReport = request.env['ir.actions.report'].sudo()

            # Get paper format
            size_name = 'A4' if template.paper_size == 'a4' else 'Letter'

            # Build footer URL (not used anymore, handled by ir_actions_report.py)
            # Keeping this code for backwards compatibility
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            footer_url = f"{base_url}/vpa/template/footer/{template.id}"

            pdf_content = IrActionsReport.with_context(
                vpa_force_zero_margins=True,
                vpa_template_id=template.id
            )._run_wkhtmltopdf(
                [html_str],
                landscape=template.paper_orientation == 'landscape',
                specific_paperformat_args={
                    '--page-size': size_name,
                    # DPI and zoom are now handled centrally in ir_actions_report.py
                    # to ensure consistency between Preview and Real Print
                },
                set_viewport_size=False
            )

            _logger.info(f"PDF generated, size: {len(pdf_content) if pdf_content else 0} bytes")

            if not pdf_content:
                return request.make_response(
                    '<h1>PDF Generation Failed</h1><p>wkhtmltopdf returned empty content.</p>',
                    headers=[('Content-Type', 'text/html')]
                )

            # Prepare response
            filename = f"{template.name}_Preview.pdf"
            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf_content)),
                ('Content-Disposition', f'attachment; filename="{filename}"')
            ]

            return request.make_response(pdf_content, headers=pdfhttpheaders)

        except Exception as e:
            _logger.error(f"PDF preview generation error: {str(e)}", exc_info=True)
            return request.make_response(
                f'<h1>PDF Generation Error</h1><p>{str(e)}</p><pre>{e.__class__.__name__}</pre>',
                headers=[('Content-Type', 'text/html')]
            )

    @http.route('/vpa/template/footer/<int:template_id>', type='http', auth='public')
    def get_footer_html(self, template_id, **kwargs):
        """Return footer HTML for wkhtmltopdf --footer-html

        This route is called by wkhtmltopdf when generating PDFs to render
        the footer at the bottom of every page.
        """
        # Use sudo() since this is called by wkhtmltopdf without authentication
        template = request.env['vpa.document.template'].sudo().browse(template_id)

        if not template.exists():
            return request.not_found()

        _logger.info(f"Rendering footer HTML for template: {template.name}")

        # Render footer-only template
        try:
            html_content = request.env['ir.ui.view'].sudo()._render_template(
                'vpa_document_layout.vpa_footer_only',
                {
                    'template': template,
                    'company': template.company_id,
                }
            )

            # Decode if bytes
            if isinstance(html_content, bytes):
                html_str = html_content.decode('utf-8')
            else:
                html_str = str(html_content)

            # Add DOCTYPE declaration for proper wkhtmltopdf rendering
            if not html_str.strip().startswith('<!DOCTYPE'):
                html_str = '<!DOCTYPE html>\n' + html_str

            return request.make_response(
                html_str,
                headers=[('Content-Type', 'text/html; charset=utf-8')]
            )
        except Exception as e:
            _logger.error(f"Footer HTML generation error: {str(e)}", exc_info=True)
            return request.make_response(
                f'<div>Footer Error: {str(e)}</div>',
                headers=[('Content-Type', 'text/html')]
            )

    @http.route('/vpa/template/preview_footer/<int:template_id>', type='http', auth='user')
    def preview_footer(self, template_id, **kwargs):
        """Show footer preview in styled container for user preview"""
        template = request.env['vpa.document.template'].browse(template_id)

        if not template.exists():
            return request.not_found()

        # Render footer preview page
        return request.render('vpa_document_layout.footer_preview_page', {
            'template': template,
        })

    @http.route('/vpa/footer/<int:footer_config_id>', type='http', auth='public')
    def get_footer_config_html(self, footer_config_id, **kwargs):
        """Return footer HTML from vpa.footer.config for wkhtmltopdf --footer-html

        This allows VPA footers to work on ANY Odoo report without needing
        a VPA Document Template - just configure a footer in Footer Settings.
        """
        # Use sudo() since this is called by wkhtmltopdf without authentication
        footer_config = request.env['vpa.footer.config'].sudo().browse(footer_config_id)

        if not footer_config.exists():
            return request.not_found()

        _logger.info(f"Rendering footer HTML from footer config: {footer_config.name}")

        company = footer_config.company_id

        # Build footer HTML based on layout type
        try:
            if footer_config.footer_layout == 'custom_html' and footer_config.custom_html:
                footer_content = footer_config._render_custom_html(company)
            elif footer_config.footer_layout == 'three_col':
                footer_content = self._render_three_col_footer(footer_config, company)
            elif footer_config.footer_layout == 'two_col':
                footer_content = self._render_two_col_footer(footer_config, company)
            else:
                footer_content = self._render_single_col_footer(footer_config, company)

            # Wrap in complete HTML document for wkhtmltopdf
            html_str = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Lato', 'Helvetica', 'Arial', sans-serif;
            font-size: {footer_config.font_size or '8pt'};
            color: {footer_config.text_color or '#666666'};
            width: 100%;
        }}
        .vpa-footer {{
            padding: 8px 15px;
            {f'border-top: 1px solid {footer_config.border_color};' if footer_config.show_border else ''}
            position: relative;
        }}
        .footer-shape {{
            position: absolute;
            bottom: 0;
            right: 0;
            width: 200px;
            height: 80px;
            background: {footer_config.shape_color or '#21b799'};
            opacity: {footer_config.shape_opacity or 0.1};
            clip-path: polygon(100% 0, 100% 100%, 0 100%);
        }}
        .footer-columns {{
            display: table;
            width: 100%;
            table-layout: fixed;
        }}
        .footer-column {{
            display: table-cell;
            vertical-align: top;
            padding: 0 10px;
        }}
        .footer-column:first-child {{ padding-left: 0; }}
        .footer-column:last-child {{ padding-right: 0; }}
        .footer-title {{
            font-weight: bold;
            margin-bottom: 5px;
            color: {footer_config.text_color or '#666666'};
        }}
        .page-number {{
            text-align: center;
            margin-top: 5px;
            font-size: 7pt;
        }}
    </style>
</head>
<body>
    <div class="vpa-footer">
        {f'<div class="footer-shape"></div>' if footer_config.show_shape else ''}
        {footer_content}
        {self._render_page_numbers() if footer_config.show_page_numbers else ''}
    </div>
</body>
</html>'''

            return request.make_response(
                html_str,
                headers=[('Content-Type', 'text/html; charset=utf-8')]
            )
        except Exception as e:
            _logger.error(f"Footer config HTML generation error: {str(e)}", exc_info=True)
            return request.make_response(
                f'<div>Footer Error: {str(e)}</div>',
                headers=[('Content-Type', 'text/html')]
            )

    def _render_three_col_footer(self, footer_config, company):
        """Render 3-column footer layout"""
        return f'''
        <div class="footer-columns">
            <div class="footer-column">
                {f'<div class="footer-title">{footer_config.column_1_title}</div>' if footer_config.column_1_title else ''}
                <div>{footer_config.column_1_content or ''}</div>
            </div>
            <div class="footer-column">
                {f'<div class="footer-title">{footer_config.column_2_title}</div>' if footer_config.column_2_title else ''}
                <div>{footer_config.column_2_content or ''}</div>
            </div>
            <div class="footer-column">
                {f'<div class="footer-title">{footer_config.column_3_title}</div>' if footer_config.column_3_title else ''}
                <div>{footer_config.column_3_content or ''}</div>
            </div>
        </div>
        '''

    def _render_two_col_footer(self, footer_config, company):
        """Render 2-column footer layout"""
        return f'''
        <div class="footer-columns">
            <div class="footer-column">
                {f'<div class="footer-title">{footer_config.column_1_title}</div>' if footer_config.column_1_title else ''}
                <div>{footer_config.column_1_content or ''}</div>
            </div>
            <div class="footer-column">
                {f'<div class="footer-title">{footer_config.column_2_title}</div>' if footer_config.column_2_title else ''}
                <div>{footer_config.column_2_content or ''}</div>
            </div>
        </div>
        '''

    def _render_single_col_footer(self, footer_config, company):
        """Render single column centered footer"""
        content_parts = []

        if footer_config.footer_type == 'internal' and footer_config.computer_generated_note:
            content_parts.append(f'<div style="font-style: italic;">{footer_config.computer_generated_note}</div>')

        if footer_config.show_bank_details and company.partner_id.bank_ids:
            bank = company.partner_id.bank_ids[0]
            bank_name = bank.bank_id.name if bank.bank_id else 'Bank'
            content_parts.append(f'<div><strong>Bank:</strong> {bank_name} | Account: {bank.acc_number or "N/A"}</div>')

        if footer_config.show_company_footer and company.report_footer:
            content_parts.append(f'<div>{company.report_footer}</div>')

        return f'<div style="text-align: center;">{"".join(content_parts)}</div>'

    def _render_page_numbers(self):
        """Render page numbers using wkhtmltopdf variables"""
        return '''
        <div class="page-number">
            Page <span class="page"></span> of <span class="topage"></span>
        </div>
        '''

    @http.route('/vpa/header/<int:footer_config_id>', type='http', auth='public')
    def get_header_config_html(self, footer_config_id, **kwargs):
        """Return header HTML from vpa.footer.config for wkhtmltopdf --header-html

        This allows VPA headers to work on ANY Odoo report without needing
        a VPA Document Template - just configure a header in Header & Footer Settings.
        """
        # Use sudo() since this is called by wkhtmltopdf without authentication
        footer_config = request.env['vpa.footer.config'].sudo().browse(footer_config_id)

        if not footer_config.exists():
            return request.not_found()

        # If header is disabled, return empty
        if not footer_config.show_header:
            return request.make_response(
                '<!DOCTYPE html><html><head></head><body></body></html>',
                headers=[('Content-Type', 'text/html; charset=utf-8')]
            )

        _logger.info(f"Rendering header HTML from footer config: {footer_config.name}")

        company = footer_config.company_id

        try:
            header_content = self._render_header_content(footer_config, company)

            # Wrap in complete HTML document for wkhtmltopdf
            html_str = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Lato', 'Helvetica', 'Arial', sans-serif;
            font-size: 10pt;
            color: {footer_config.header_text_color or '#333333'};
            width: 100%;
            background: {footer_config.header_background_color or '#ffffff'};
        }}
        .vpa-header {{
            padding: 10px 15px;
            {f'border-bottom: 1px solid {footer_config.header_border_color};' if footer_config.header_border_bottom else ''}
            position: relative;
            min-height: 20mm;
        }}
        .header-standard {{
            display: table;
            width: 100%;
        }}
        .header-left {{
            display: table-cell;
            vertical-align: middle;
            width: 50%;
        }}
        .header-right {{
            display: table-cell;
            vertical-align: middle;
            width: 50%;
            text-align: right;
        }}
        .header-centered {{
            text-align: center;
        }}
        .header-minimal {{
            text-align: left;
        }}
        .company-logo {{
            max-height: 50px;
            max-width: 150px;
        }}
        .company-name {{
            font-size: 14pt;
            font-weight: bold;
            color: {footer_config.header_text_color or '#333333'};
        }}
        .company-details {{
            font-size: 8pt;
            color: {footer_config.header_text_color or '#666666'};
            margin-top: 5px;
        }}
        .document-title {{
            font-size: 12pt;
            font-weight: bold;
            margin-top: 5px;
        }}
        .header-date {{
            font-size: 9pt;
            color: {footer_config.header_text_color or '#666666'};
        }}
    </style>
</head>
<body>
    <div class="vpa-header">
        {header_content}
    </div>
</body>
</html>'''

            return request.make_response(
                html_str,
                headers=[('Content-Type', 'text/html; charset=utf-8')]
            )
        except Exception as e:
            _logger.error(f"Header config HTML generation error: {str(e)}", exc_info=True)
            return request.make_response(
                f'<div>Header Error: {str(e)}</div>',
                headers=[('Content-Type', 'text/html')]
            )

    def _render_header_content(self, footer_config, company):
        """Render header content based on layout type"""
        from datetime import date

        # Get company logo as data URI if available
        logo_html = ''
        if footer_config.header_show_logo and company.logo:
            logo_data = image_data_uri(company.logo)
            logo_html = f'<img src="{logo_data}" class="company-logo" alt="{company.name}"/>'

        # Company name
        company_name_html = ''
        if footer_config.header_show_company_name:
            company_name_html = f'<div class="company-name">{company.name}</div>'

        # Company details (address, phone, email)
        company_details_html = ''
        if footer_config.header_show_company_details:
            details = []
            if company.street:
                details.append(company.street)
            if company.city:
                city_line = company.city
                if company.state_id:
                    city_line += f', {company.state_id.name}'
                if company.zip:
                    city_line += f' {company.zip}'
                details.append(city_line)
            if company.phone:
                details.append(f'Phone: {company.phone}')
            if company.email:
                details.append(f'Email: {company.email}')
            if details:
                company_details_html = f'<div class="company-details">{" | ".join(details)}</div>'

        # Document title
        title_html = ''
        if footer_config.header_show_document_title:
            title_text = footer_config.header_custom_title or 'Document'
            title_html = f'<div class="document-title">{title_text}</div>'

        # Date
        date_html = ''
        if footer_config.header_show_date:
            today = date.today()
            if footer_config.header_date_format == 'short':
                date_str = today.strftime('%m/%d/%Y')
            elif footer_config.header_date_format == 'long':
                date_str = today.strftime('%B %d, %Y')
            else:  # medium (default)
                date_str = today.strftime('%b %d, %Y')
            date_html = f'<div class="header-date">{date_str}</div>'

        # Layout-specific rendering
        if footer_config.header_layout == 'custom_html' and footer_config.header_custom_html:
            return self._render_custom_header_html(footer_config, company)
        elif footer_config.header_layout == 'centered':
            return f'''
            <div class="header-centered">
                {logo_html}
                {company_name_html}
                {company_details_html}
                {title_html}
                {date_html}
            </div>
            '''
        elif footer_config.header_layout == 'minimal':
            return f'''
            <div class="header-minimal">
                {company_name_html}
                {date_html}
            </div>
            '''
        else:  # standard (default)
            return f'''
            <div class="header-standard">
                <div class="header-left">
                    {logo_html}
                    {company_name_html}
                    {company_details_html}
                </div>
                <div class="header-right">
                    {title_html}
                    {date_html}
                </div>
            </div>
            '''

    def _render_custom_header_html(self, footer_config, company):
        """Render custom header HTML with placeholder substitution"""
        from datetime import date

        html = footer_config.header_custom_html or ''

        # Get company logo as data URI
        logo_html = ''
        if company.logo:
            logo_data = image_data_uri(company.logo)
            logo_html = f'<img src="{logo_data}" style="max-height:50px;" alt="{company.name}"/>'

        # Date formatting
        today = date.today()
        if footer_config.header_date_format == 'short':
            date_str = today.strftime('%m/%d/%Y')
        elif footer_config.header_date_format == 'long':
            date_str = today.strftime('%B %d, %Y')
        else:
            date_str = today.strftime('%b %d, %Y')

        # Replace placeholders
        replacements = {
            '{{company_name}}': company.name or '',
            '{{company_logo}}': logo_html,
            '{{document_title}}': footer_config.header_custom_title or 'Document',
            '{{date}}': date_str,
        }

        for placeholder, value in replacements.items():
            html = html.replace(placeholder, str(value))

        return html
