from odoo import http, _
from odoo.http import request
from odoo.modules.module import get_resource_path
from odoo.tools import pdf


class StockBarcodeController(http.Controller):

    @http.route('/stock_barcode/scan_from_main_menu', type='json', auth='user')
    def main_menu(self, barcode, **kw):
        """ Receive a barcode scanned from the main menu and return the appropriate
            action (open an existing / new picking) or warning.
        """



        product = request.env['product.template'].search([('barcode', '=', barcode),])
        return product.id
