# -*- coding: utf-8 -*-
from odoo import models
import logging

_logger = logging.getLogger(__name__)

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    _logger.warning("WeasyPrint not available. Falling back to wkhtmltopdf for PDF generation.")


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        """Override to use WeasyPrint for VPA layout reports"""
        # Check if this report uses VPA layout
        if self._is_vpa_layout_report(res_ids):
            if WEASYPRINT_AVAILABLE:
                return self._render_vpa_weasyprint(report_ref, data, res_ids)

        # Fall back to default wkhtmltopdf for other reports
        return super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids)

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

    def _render_vpa_weasyprint(self, report_ref, data, res_ids):
        """Render PDF using WeasyPrint for better CSS support"""
        _logger.info("Rendering PDF with WeasyPrint for VPA layout")

        # Get HTML content using Odoo's QWeb rendering
        html_content, content_type = self._render_qweb_html(report_ref, data, res_ids)

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
