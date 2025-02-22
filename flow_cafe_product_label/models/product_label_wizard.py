from odoo import models, fields, api, _
from odoo.exceptions import UserError 


class ProductLabelWizard(models.TransientModel):
    _inherit = "product.label.layout"

    print_format = fields.Selection(selection_add=[
        ('dymo_new', 'Dymo New')
    ], ondelete={'dymo_new': 'set default'})

    def _prepare_report_data(self):
        xml_id, data = super()._prepare_report_data()

        print(f"DEBUG: print_format value = {self.print_format}")  # Debugging

        if self.print_format == 'dymo_new':
            xml_id = 'product.report_product_template_label_dymo'
                              
        return xml_id, data

    def process(self):
        self.ensure_one()
        xml_id, data = self._prepare_report_data()
        
        if not xml_id:
            raise UserError(_('Unable to find report template for format: %s', self.print_format))

        data.update({'print_format': self.print_format})  # Ensure print_format is passed

        # Correctly fetching the report action
        report_action = self.env.ref(xml_id)
        if not report_action or report_action._name != 'ir.actions.report':
            raise UserError(_('Invalid report action: %s', xml_id))

        return report_action.report_action(self, data=data)

