# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


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
