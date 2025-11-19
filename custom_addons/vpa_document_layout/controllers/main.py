# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class VPATemplatePreview(http.Controller):

    @http.route('/vpa/template/preview/<int:template_id>', type='http', auth='user')
    def preview_template(self, template_id, **kwargs):
        """Generate preview for a VPA document template"""
        template = request.env['vpa.document.template'].browse(template_id)

        if not template.exists():
            return request.not_found()

        # Get a sample document based on document type
        sample_doc = template._get_sample_document()

        if not sample_doc:
            return request.render('vpa_document_layout.template_preview_no_data', {
                'template': template,
            })

        # Render the report
        report_action = template.report_action_id
        if report_action:
            pdf_content = request.env['ir.actions.report']._render_qweb_pdf(
                report_action.report_name,
                sample_doc.ids
            )[0]

            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf_content)),
            ]
            return request.make_response(pdf_content, headers=pdfhttpheaders)

        return request.not_found()
