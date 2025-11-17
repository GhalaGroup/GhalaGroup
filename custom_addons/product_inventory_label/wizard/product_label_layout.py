from odoo import models, fields, api

class ProductLabel(models.TransientModel):
    _inherit = 'product.label.layout'
    print_format = fields.Selection(
        selection_add=[('inventory_label', 'Inventory Label')],
        ondelete={'inventory_label':'set default'}
    )
    
    def _prepare_report_data(self):
        xml_id,data = super()._prepare_report_data()
        if 'inventory_label' in self.print_format:
            xml_id = 'product_inventory_label.product_inventory_label'
            
        return xml_id,data