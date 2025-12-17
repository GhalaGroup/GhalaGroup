# -*- coding: utf-8 -*-
from odoo import models
import logging
import subprocess
import tempfile
import os

_logger = logging.getLogger(__name__)

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    # Don't log warning at module load - only log when actually attempting to use it

# Check if Playwright is available
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    # Don't log warning at module load - only log when actually attempting to use it


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        """Override to redirect to VPA template if marked as default"""
        # Map standard report XML IDs to document types
        standard_report_map = {
            'sale.report_saleorder': ('sale.order', 'quotation'),
            'sale.action_report_saleorder': ('sale.order', 'quotation'),
            'account.account_invoices': ('account.move', 'invoice'),
            'purchase.action_report_purchase_order': ('purchase.order', 'purchase_order'),
            'stock.action_report_delivery': ('stock.picking', 'delivery'),
            'mrp.report_mrporder': ('mrp.production', 'manufacturing_order'),
            'mrp.action_report_production_order': ('mrp.production', 'manufacturing_order'),
        }

        # Check if this is a standard report that might have a VPA default
        report_name = report_ref if isinstance(report_ref, str) else report_ref.report_name

        if report_name in standard_report_map:
            model_name, doc_type = standard_report_map[report_name]

            # Get the company from the first record
            if res_ids and len(res_ids) > 0:
                record = self.env[model_name].browse(res_ids[0])
                company_id = record.company_id.id if hasattr(record, 'company_id') else self.env.company.id

                # Search for default VPA template
                vpa_template = self.env['vpa.document.template'].search([
                    ('company_id', '=', company_id),
                    ('document_type', '=', doc_type),
                    ('is_default_print', '=', True),
                    ('active', '=', True),
                ], limit=1)

                if vpa_template and vpa_template.report_action_id:
                    _logger.info(f"🔄 Redirecting {report_name} to VPA template: {vpa_template.name}")
                    # Use the VPA template report instead
                    return vpa_template.report_action_id._render_qweb_pdf(
                        vpa_template.report_action_id,
                        res_ids=res_ids,
                        data=data
                    )

        # No VPA template found, use standard report
        return super(IrActionsReport, self)._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

    def _run_wkhtmltopdf(
            self,
            bodies,
            report_ref=False,
            header=None,
            footer=None,
            landscape=False,
            specific_paperformat_args=None,
            set_viewport_size=False):
        """Override to inject VPA header/footer for VPA templates"""
        footer_config_id = self.env.context.get('vpa_footer_config_id')
        _logger.info(f"🔍 _run_wkhtmltopdf called - header param: {type(header).__name__ if header else None}, footer param: {type(footer).__name__ if footer else None}, vpa_force_zero_margins: {self.env.context.get('vpa_force_zero_margins')}, vpa_footer_config_id: {footer_config_id}")

        # For VPA templates, replace header with VPA header HTML (using same mechanism as Odoo)
        if self.env.context.get('vpa_force_zero_margins'):
            # Clear Odoo's default footer - we use --footer-html URL instead
            if footer is not None:
                _logger.info(f"⚠️  VPA template has footer parameter - clearing it to use --footer-html URL instead")
                footer = None

            # Generate VPA header HTML and pass as header parameter (Odoo will write to temp file)
            if footer_config_id:
                footer_config = self.env['vpa.footer.config'].sudo().browse(footer_config_id)
                if footer_config.exists() and footer_config.show_header:
                    # Generate header HTML - this will be written to temp file by parent method
                    header = self._generate_header_html(footer_config)
                    _logger.info(f"✅ Generated VPA header HTML ({len(header)} chars) for footer_config_id={footer_config_id}")
                else:
                    _logger.info(f"⚠️ Header disabled or config not found for footer_config_id={footer_config_id}")
                    header = None
            else:
                # Also clear header if no footer_config
                if header is not None:
                    _logger.info(f"⚠️  VPA template has header parameter but no footer_config - clearing it")
                    header = None

        return super()._run_wkhtmltopdf(
            bodies,
            report_ref=report_ref,
            header=header,
            footer=footer,
            landscape=landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size
        )

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        """Override to use custom PDF generation for VPA layout reports"""
        # Get the actual report record to access report_name and model
        report = self._get_report(report_ref)
        report_name = report.report_name if report else (self.report_name or '')
        model_name = report.model if report else (self.model or '')

        _logger.info(f"🔍 PDF Generation - report_ref: {report_ref}, report_name: {report_name}, model: {model_name}, context.vpa_force_zero_margins: {self.env.context.get('vpa_force_zero_margins')}")

        # Skip if already processed
        if self.env.context.get('vpa_force_zero_margins'):
            _logger.info("VPA context flag already set - proceeding to super()")
            return super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids)

        # Check if this is a VPA template report by checking the report_name
        is_vpa_template = 'vpa_document_layout.report_template_' in (report_name or '')
        _logger.info(f"🔍 is_vpa_template={is_vpa_template}, checking if '{report_name}' contains 'vpa_document_layout.report_template_'")

        if is_vpa_template:
            # Extract template ID from report_name (format: vpa_document_layout.report_template_3)
            try:
                template_id = int(report_name.split('_')[-1])
                _logger.info(f"Extracted template ID: {template_id}")
            except (ValueError, IndexError):
                _logger.warning(f"Could not extract template ID from report_name: {report_name}")
                template_id = None

            _logger.info("VPA template detected - setting vpa_force_zero_margins context flag")
            # Set context flags so _build_wkhtmltopdf_args knows to use footer-html
            return self.with_context(
                vpa_force_zero_margins=True,
                vpa_template_id=template_id
            )._render_qweb_pdf_prepare_streams(report_ref, data, res_ids)

        # NEW: Check if company has a VPA footer config for ALL reports
        # This applies VPA footers globally without needing a VPA template
        if res_ids and model_name:
            try:
                docs = self.env[model_name].browse(res_ids[:1])
                _logger.info(f"🔍 VPA Footer Check - model: {model_name}, res_ids: {res_ids[:3]}, docs exists: {bool(docs)}")

                # Safely get company from document
                company = None
                if docs and docs.exists():
                    if hasattr(docs, 'company_id') and docs.company_id:
                        company = docs.company_id
                        _logger.info(f"🔍 Got company from doc: {company.name} (ID: {company.id})")

                if not company:
                    company = self.env.company
                    _logger.info(f"🔍 Using current company: {company.name} (ID: {company.id})")

                # Get the appropriate footer config for this report
                _logger.info(f"🔍 Looking for footer config for company_id={company.id}, report={report_name}")

                footer_config = self.env['vpa.footer.config'].get_footer_for_report(
                    company.id,
                    report_name
                )

                if footer_config:
                    _logger.info(f"✅ Found VPA footer config '{footer_config.name}' (ID: {footer_config.id}) for report {report_name}")
                    return self.with_context(
                        vpa_force_zero_margins=True,
                        vpa_footer_config_id=footer_config.id
                    )._render_qweb_pdf_prepare_streams(report_ref, data, res_ids)
                else:
                    _logger.info(f"ℹ️  No VPA footer config found for company {company.name} (ID: {company.id})")
            except Exception as e:
                _logger.warning(f"Could not check VPA footer config: {e}", exc_info=True)
        else:
            _logger.info(f"⚠️  Skipping VPA footer check - res_ids: {res_ids}, model_name: {model_name}")

        # Fall back to default wkhtmltopdf for all reports
        return super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids)

    def _is_vpa_template_report(self):
        """Check if this is a VPA document template report"""
        return 'vpa_document_layout.report_template_' in (self.report_name or '')

    def _prepare_html(self, html, report_model=None):
        """Override to add wkhtmltopdf-specific options for VPA templates"""
        # For VPA templates, we need to ensure wkhtmltopdf uses zero margins
        if self._is_vpa_template_report():
            # Force the command_args to include zero margins
            if hasattr(self, 'env'):
                # Store original command_args
                pass
        return super()._prepare_html(html, report_model=report_model)

    def _build_wkhtmltopdf_args(self, paperformat_id, landscape=False, specific_paperformat_args=None, set_viewport_size=False):
        """Override wkhtmltopdf args to force zero margins for VPA templates"""
        command_args = super()._build_wkhtmltopdf_args(
            paperformat_id,
            landscape=landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size
        )

        _logger.info(f"Original wkhtmltopdf args: {command_args}")

        # For VPA template reports, force zero margins using context flag
        if self.env.context.get('vpa_force_zero_margins'):
            _logger.info("✅ Forcing zero margins for VPA template (context flag detected)")

            # Remove margin/spacing arguments, DPI, zoom, --disable-local-file-access, AND --quiet
            new_args = []
            skip_next = False
            for i, arg in enumerate(command_args):
                if skip_next:
                    skip_next = False
                    continue

                # Check if this arg is a margin/spacing parameter
                if arg.startswith('--margin-') or arg in ['--header-spacing', '--footer-spacing']:
                    skip_next = True  # Skip the value too
                    continue

                # Remove DPI and zoom to ensure consistent rendering between Preview and Real Print
                if arg in ['--dpi', '--zoom']:
                    skip_next = True  # Skip the value too
                    continue

                # Remove --disable-local-file-access so footer-html can fetch from localhost
                if arg == '--disable-local-file-access':
                    continue

                # Remove --quiet to see wkhtmltopdf errors
                if arg == '--quiet':
                    continue

                new_args.append(arg)

            command_args = new_args

            # Add consistent DPI and zoom for all VPA templates
            # This ensures Preview and Real Print render identically
            command_args.extend([
                '--dpi', '96',   # Match paper format DPI
                '--zoom', '1.0',  # No zoom scaling
            ])

            # Get template ID or footer config ID for footer
            template_id = self.env.context.get('vpa_template_id')
            footer_config_id = self.env.context.get('vpa_footer_config_id')
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

            footer_url = None
            if template_id:
                # Use VPA document template footer
                footer_url = f"{base_url}/vpa/template/footer/{template_id}"
                _logger.info(f"✅ Using VPA template footer: {footer_url}")
            elif footer_config_id:
                # Use VPA footer config (global footer for all reports)
                footer_url = f"{base_url}/vpa/footer/{footer_config_id}"
                _logger.info(f"✅ Using VPA footer config: {footer_url}")

            # Get header height if footer_config has header enabled
            # Note: Header HTML is passed via header parameter in _run_wkhtmltopdf, not --header-html URL
            header_height = '0'
            has_header = False
            if footer_config_id:
                footer_config = self.env['vpa.footer.config'].sudo().browse(footer_config_id)
                _logger.info(f"🔍 Header check: footer_config_id={footer_config_id}, exists={footer_config.exists()}, show_header={footer_config.show_header if footer_config.exists() else 'N/A'}")
                if footer_config.exists() and footer_config.show_header:
                    has_header = True
                    header_height = footer_config.header_height or '25mm'
                    _logger.info(f"✅ VPA header enabled, height: {header_height}")
                else:
                    _logger.info(f"⚠️ Header disabled or config not found for footer_config_id={footer_config_id}")

            if footer_url or has_header:
                command_args.extend([
                    '--enable-local-file-access',
                    '--margin-top', header_height if has_header else '0',
                    '--margin-bottom', '30mm' if footer_url else '0',  # Reserve space for footer
                    '--margin-left', '0',
                    '--margin-right', '0',
                ])
                # Header is handled via header parameter -> temp file in _run_wkhtmltopdf
                # Footer uses --footer-html URL
                if has_header:
                    command_args.extend([
                        '--header-spacing', '0',
                    ])
                if footer_url:
                    command_args.extend([
                        '--footer-spacing', '0',
                        '--footer-html', footer_url
                    ])
            else:
                # No header or footer
                command_args.extend([
                    '--margin-top', '0',
                    '--margin-bottom', '0',
                    '--margin-left', '0',
                    '--margin-right', '0',
                    '--header-spacing', '0',
                    '--footer-spacing', '0',
                ])

            _logger.info(f"✅ Final wkhtmltopdf args: {command_args}")
        else:
            _logger.info("❌ No vpa_force_zero_margins context flag - using default margins")

        return command_args

    def _generate_header_html(self, footer_config):
        """Generate header HTML for wkhtmltopdf --header-html"""
        from datetime import date
        from odoo.tools.image import image_data_uri

        company = footer_config.company_id

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

        # Layout-specific content
        if footer_config.header_layout == 'centered':
            header_content = f'''
            <div class="header-centered">
                {logo_html}
                {company_name_html}
                {company_details_html}
                {title_html}
                {date_html}
            </div>
            '''
        elif footer_config.header_layout == 'minimal':
            header_content = f'''
            <div class="header-minimal">
                {company_name_html}
                {date_html}
            </div>
            '''
        else:  # standard (default)
            header_content = f'''
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

        # Full HTML document
        return f'''<!DOCTYPE html>
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
        }}
        .company-details {{
            font-size: 8pt;
            margin-top: 5px;
        }}
        .document-title {{
            font-size: 12pt;
            font-weight: bold;
            margin-top: 5px;
        }}
        .header-date {{
            font-size: 9pt;
        }}
    </style>
</head>
<body>
    <div class="vpa-header">
        {header_content}
    </div>
</body>
</html>'''

    def _is_vpa_layout_report(self, res_ids):
        """Check if report should use VPA layout"""
        # Get the first document to check its company's layout
        if not res_ids:
            return False

        try:
            # Get report's model
            if self.model:
                docs = self.env[self.model].browse(res_ids[:1])
                if docs and hasattr(docs[0], 'company_id'):
                    company = docs[0].company_id
                    if company.external_report_layout_id:
                        # Check if company is using VPA layout
                        return 'vpa' in company.external_report_layout_id.key.lower()
        except Exception as e:
            _logger.debug(f"Could not determine VPA layout: {e}")

        return False

    def _render_vpa_playwright(self, report_ref, data, res_ids):
        """Render PDF using Playwright with zero margins"""
        _logger.info("Rendering PDF with Playwright for VPA layout - zero margins")

        # Get HTML content using Odoo's QWeb rendering (docids, then data)
        html_content, content_type = self._render_qweb_html(report_ref, res_ids, data)

        if isinstance(html_content, bytes):
            html_content = html_content.decode('utf-8')

        try:
            with sync_playwright() as p:
                # Launch with args suitable for Docker environment
                browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-dev-shm-usage', '--no-sandbox', '--disable-setuid-sandbox']
                )
                page = browser.new_page()

                # Set content and wait for it to load (use 'load' instead of 'networkidle' for better compatibility)
                page.set_content(html_content, wait_until='load')

                # Generate PDF with zero margins
                pdf_content = page.pdf(
                    format='A4',
                    margin={
                        'top': '0px',
                        'right': '0px',
                        'bottom': '0px',
                        'left': '0px'
                    },
                    print_background=True,
                    prefer_css_page_size=False
                )

                browser.close()
                return [(0, pdf_content)]
        except Exception as e:
            _logger.error(f"Playwright rendering failed: {e}. Falling back to wkhtmltopdf")
            return super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids)

    def _render_vpa_weasyprint(self, report_ref, data, res_ids):
        """Render PDF using WeasyPrint for better CSS support"""
        _logger.info("Rendering PDF with WeasyPrint for VPA layout")

        # Get HTML content using Odoo's QWeb rendering (docids, then data)
        html_content, content_type = self._render_qweb_html(report_ref, res_ids, data)

        if isinstance(html_content, bytes):
            html_content = html_content.decode('utf-8')

        # Configure fonts for WeasyPrint
        font_config = FontConfiguration()

        # Render with WeasyPrint
        try:
            html = HTML(string=html_content, base_url=self.env['ir.config_parameter'].sudo().get_param('web.base.url'))
            pdf_content = html.write_pdf(font_config=font_config)

            return [(0, pdf_content)]
        except Exception as e:
            _logger.error(f"WeasyPrint rendering failed: {e}. Falling back to wkhtmltopdf")
            # Fall back to wkhtmltopdf if WeasyPrint fails
            return super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids)
