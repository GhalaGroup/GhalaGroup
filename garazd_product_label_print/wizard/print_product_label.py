# Copyright © 2023 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (<support@garazd.biz>)
# @author: Iryna Razumovska (<support@garazd.biz>)
# License OPL-1 (https://www.odoo.com/documentation/15.0/legal/licenses.html).

import base64

from datetime import datetime, timedelta

from odoo import api, models
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

LABEL_ATTACHMENT_NAME = 'Product Label Direct Printing'


class PrintProductLabel(models.TransientModel):
    _inherit = "print.product.label"

    def action_print_direct(self):
        """Print labels directly without download."""
        self.ensure_one()
        report = self._prepare_report()
        pdf_data = report._render_qweb_pdf(report, *self._get_report_action_params())
        attachment = self.env['ir.attachment'].create({
            'name': LABEL_ATTACHMENT_NAME,
            'type': 'binary',
            'datas': base64.b64encode(pdf_data[0]),
            'mimetype': 'application/pdf',
            'public': False,
        })
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action = {
            'type': 'ir.actions.act_url',
            'url': f'{base_url}/print_label/{attachment.id}',
            'target': 'new',
        }
        return action

    @api.autovacuum
    def _gc_print_label_attachments(self):
        timeout_ago = datetime.utcnow() - timedelta(days=1)
        domain = [
            ('name', '=', LABEL_ATTACHMENT_NAME),
            ('mimetype', '=', 'application/pdf'),
            ('create_date', '<', timeout_ago.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
        ]
        return self.env['ir.attachment'].sudo().search(domain).unlink()
