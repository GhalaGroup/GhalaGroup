# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

import json
import logging

import requests

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class LabelDesignerController(http.Controller):

    @http.route('/vpa_label_designer/preview', type='jsonrpc', auth='user')
    def zpl_preview(self, zpl_code, dpi=8, width=4, height=2):
        """Proxy to Labelary API for ZPL visual preview.

        Args:
            zpl_code: ZPL code string
            dpi: DPI setting for Labelary (8 = 203dpi, 12 = 300dpi, 24 = 600dpi)
            width: Label width in inches
            height: Label height in inches

        Returns:
            dict with base64-encoded PNG image or error
        """
        try:
            url = f'http://api.labelary.com/v1/printers/{dpi}dpmm/labels/{width}x{height}/0/'
            response = requests.post(
                url,
                data=zpl_code.encode('utf-8'),
                headers={'Accept': 'image/png'},
                timeout=10,
            )

            if response.status_code == 200:
                import base64
                image_b64 = base64.b64encode(response.content).decode('utf-8')
                return {'success': True, 'image': image_b64}
            else:
                return {
                    'success': False,
                    'error': f'Labelary API returned status {response.status_code}',
                }

        except requests.Timeout:
            return {'success': False, 'error': 'Labelary API request timed out'}
        except requests.ConnectionError:
            return {'success': False, 'error': 'Could not connect to Labelary API'}
        except Exception as e:
            _logger.exception('Error calling Labelary API')
            return {'success': False, 'error': str(e)}

    @http.route('/vpa_label_designer/print_network', type='jsonrpc', auth='user')
    def print_network(self, printer_id, zpl_data):
        """Send ZPL data to a network printer.

        Args:
            printer_id: ID of vpa.printer.config record
            zpl_data: ZPL code string or list of ZPL strings

        Returns:
            dict with success status
        """
        printer = request.env['vpa.printer.config'].browse(int(printer_id))
        if not printer.exists():
            return {'success': False, 'error': 'Printer not found'}

        try:
            result = printer.send_zpl(zpl_data)
            return {'success': True, 'result': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
