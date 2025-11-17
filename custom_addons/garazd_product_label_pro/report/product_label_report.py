from odoo import models


class ReportGarazdProductLabelFromTemplate(models.AbstractModel):
    _name = 'report.garazd_product_label.report_product_label_from_template'
    _description = 'Custom Product Label Report'

    def _get_report_values(self, docids, data):
        labels = self.env['print.product.label.line'].browse(data.get('ids', []))
        return {
            'doc_model': 'print.product.label.line',
            'doc_ids': labels.ids,
            'docs': labels,
            'data': data.get('data'),
        }
