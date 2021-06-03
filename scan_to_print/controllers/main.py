from odoo import http, _
from odoo.http import request



class StockBarcodeController(http.Controller):

    @http.route('/scan_to_print/scan_from_main_menu_mod', type='json', auth='user')
    def main_menu(self, barcode, **kw):
        """ Receive a barcode scanned from the main menu and return the appropriate
            action (open an existing / new picking) or warning.
        """
        product = request.env['product.product'].search([('barcode', '=', barcode)])
        if product.id:
            return product.id
        else:
            vendor = request.env['product.product'].search([('x_studio_vendor_barcode', '=', barcode)])
            if vendor:
                return 'vendor'
            else:
                return False

