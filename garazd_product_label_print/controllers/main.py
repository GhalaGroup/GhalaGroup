# Copyright © 2023 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (<support@garazd.biz>)
# @author: Iryna Razumovska (<support@garazd.biz>)
# License OPL-1 (https://www.odoo.com/documentation/15.0/legal/licenses.html).

from odoo import http
from odoo.http import request

from ..wizard.print_product_label import LABEL_ATTACHMENT_NAME


class PrintPDF(http.Controller):

    @http.route(
        '/print_label/<string:attachment_id>',
        type='http',
        auth='user',
        sitemap=False,
    )
    def print_label_pdf(self, attachment_id=None, **kwargs):
        if not attachment_id:
            return request.not_found()

        try:
            attachment_id = int(attachment_id)
        except:
            return request.not_found()

        attachment = request.env['ir.attachment'].sudo().search([
            ('name', '=', LABEL_ATTACHMENT_NAME),
            ('mimetype', '=', 'application/pdf'),
            ('id', '=', attachment_id),
        ])

        if not attachment:
            return request.not_found()

        pdf_url = f'/web/image/{attachment_id}'
        return request.render(
            "garazd_product_label_print.print_product_label_pdf_template",
            {'title': 'Print Product Labels', 'pdf_url': pdf_url},
        )
