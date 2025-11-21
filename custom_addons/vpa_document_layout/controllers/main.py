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

            if not sample_doc:
                # Fallback to hardcoded preview if no sample document
                html_content = request.env['ir.ui.view']._render_template(
                    'vpa_document_layout.vpa_template_preview_layout',
                    {
                        'template': template,
                        'company': template.company_id,
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

            # Build footer URL
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
