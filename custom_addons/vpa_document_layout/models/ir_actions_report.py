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
        """Override to log footer parameter and see if it conflicts with --footer-html"""
        _logger.info(f"🔍 _run_wkhtmltopdf called with footer parameter: {footer is not None}, vpa_force_zero_margins: {self.env.context.get('vpa_force_zero_margins')}")

        # For VPA templates, we use --footer-html instead of footer parameter
        # So we need to clear the footer parameter to avoid conflicts
        if self.env.context.get('vpa_force_zero_margins') and footer is not None:
            _logger.info(f"⚠️  VPA template has footer parameter - clearing it to use --footer-html instead")
            footer = None

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
        _logger.info(f"🔍 PDF Generation - report_ref: {report_ref}, report_name: {self.report_name}, context.vpa_force_zero_margins: {self.env.context.get('vpa_force_zero_margins')}")

        # Skip if already processed
        if self.env.context.get('vpa_force_zero_margins'):
            _logger.info("VPA context flag already set - proceeding to super()")
            return super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids)

        # Check if this is a VPA template report by checking the report_name
        is_vpa_template = 'vpa_document_layout.report_template_' in (self.report_name or '')
        _logger.info(f"🔍 is_vpa_template={is_vpa_template}, checking if '{self.report_name}' contains 'vpa_document_layout.report_template_'")

        if is_vpa_template:
            # Extract template ID from report_name (format: vpa_document_layout.report_template_3)
            try:
                template_id = int(self.report_name.split('_')[-1])
                _logger.info(f"Extracted template ID: {template_id}")
            except (ValueError, IndexError):
                _logger.warning(f"Could not extract template ID from report_name: {self.report_name}")
                template_id = None

            _logger.info("VPA template detected - setting vpa_force_zero_margins context flag")
            # Set context flags so _build_wkhtmltopdf_args knows to use footer-html
            return self.with_context(
                vpa_force_zero_margins=True,
                vpa_template_id=template_id
            )._render_qweb_pdf_prepare_streams(report_ref, data, res_ids)

        # NEW: Check if company has a VPA footer config for ALL reports
        # This applies VPA footers globally without needing a VPA template
        if res_ids and self.model:
            try:
                docs = self.env[self.model].browse(res_ids[:1])
                _logger.info(f"🔍 VPA Footer Check - model: {self.model}, res_ids: {res_ids[:3]}, docs exists: {bool(docs)}")

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
                report_name = self.report_name or ''
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

            if footer_url:
                command_args.extend([
                    '--enable-local-file-access',
                    '--margin-top', '0',
                    '--margin-bottom', '30mm',  # Reserve space for footer
                    '--margin-left', '0',
                    '--margin-right', '0',
                    '--header-spacing', '0',
                    '--footer-spacing', '0',
                    '--footer-html', footer_url,
                ])
            else:
                # No footer
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
