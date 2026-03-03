# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

import logging
import socket

import requests as http_requests

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PrinterConfig(models.Model):
    _name = 'vpa.printer.config'
    _description = 'Zebra Printer Configuration'
    _order = 'is_default desc, name'

    name = fields.Char(string='Printer Name', required=True)
    print_method = fields.Selection([
        ('network', 'Direct Network (TCP/IP)'),
        ('browser_print', 'Zebra Browser Print SDK'),
    ], string='Print Method', required=True, default='network')

    # Network settings
    printer_ip = fields.Char(string='Printer IP Address')
    printer_port = fields.Integer(string='Port', default=9100)

    # Browser Print settings
    browser_print_url = fields.Char(string='Browser Print URL',
                                    default='http://localhost:9101')
    browser_print_device = fields.Char(string='Device Name',
                                       help='Specific printer name as registered in Browser Print')

    default_dpi = fields.Selection([
        ('203', '203 DPI'),
        ('300', '300 DPI'),
        ('600', '600 DPI'),
    ], string='Default DPI', default='203')

    is_default = fields.Boolean(string='Default Printer', default=False)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    @api.onchange('is_default')
    def _onchange_is_default(self):
        if self.is_default and self._origin.id:
            # Clear other defaults in same company
            others = self.search([
                ('id', '!=', self._origin.id),
                ('is_default', '=', True),
                ('company_id', '=', self.company_id.id),
            ])
            if others:
                return {
                    'warning': {
                        'title': 'Default Printer',
                        'message': f'Setting this as default will remove default from: {", ".join(others.mapped("name"))}',
                    }
                }

    def write(self, vals):
        res = super().write(vals)
        if vals.get('is_default'):
            # Ensure only one default per company
            for rec in self:
                self.search([
                    ('id', '!=', rec.id),
                    ('is_default', '=', True),
                    ('company_id', '=', rec.company_id.id),
                ]).write({'is_default': False})
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.is_default:
                self.search([
                    ('id', '!=', rec.id),
                    ('is_default', '=', True),
                    ('company_id', '=', rec.company_id.id),
                ]).write({'is_default': False})
        return records

    def action_test_connection(self):
        """Test TCP connection to network printer."""
        self.ensure_one()
        if self.print_method != 'network':
            raise UserError('Connection test is only available for network printers.')
        if not self.printer_ip:
            raise UserError('Please enter the printer IP address.')

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.printer_ip, self.printer_port))
            sock.close()

            if result == 0:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Connection Successful',
                        'message': f'Successfully connected to {self.printer_ip}:{self.printer_port}',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(
                    f'Could not connect to {self.printer_ip}:{self.printer_port}. '
                    f'Please check the printer is powered on and connected to the network.'
                )
        except socket.timeout:
            raise UserError(
                f'Connection to {self.printer_ip}:{self.printer_port} timed out. '
                f'Please check the printer IP address and network connectivity.'
            )
        except OSError as e:
            raise UserError(f'Network error: {e}')

    def send_zpl(self, zpl_data):
        """Send ZPL data to network printer via TCP socket.

        Args:
            zpl_data: str or list of str - ZPL code to send

        Returns:
            dict: Action result (notification or Browser Print client action)
        """
        self.ensure_one()

        if isinstance(zpl_data, list):
            zpl_data = '\n'.join(zpl_data)

        if self.print_method == 'network':
            return self._send_network(zpl_data)
        elif self.print_method == 'browser_print':
            return self._send_browser_print(zpl_data)

    def _send_network(self, zpl_data):
        """Send ZPL via TCP socket to network printer."""
        if not self.printer_ip:
            raise UserError('Printer IP address is not configured.')

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.printer_ip, self.printer_port))
            sock.sendall(zpl_data.encode('utf-8'))
            sock.close()

            _logger.info('ZPL sent to %s:%s (%d bytes)',
                         self.printer_ip, self.printer_port, len(zpl_data))

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Print Job Sent',
                    'message': f'ZPL data sent to {self.name} ({self.printer_ip}:{self.printer_port})',
                    'type': 'success',
                    'sticky': False,
                }
            }
        except socket.timeout:
            raise UserError(f'Connection to {self.printer_ip}:{self.printer_port} timed out.')
        except OSError as e:
            raise UserError(f'Failed to send print job: {e}')

    def _send_browser_print(self, zpl_data):
        """Return client action for Browser Print SDK (handled in browser JS)."""
        return {
            'type': 'ir.actions.client',
            'tag': 'vpa_label_designer.browser_print',
            'params': {
                'zpl_data': zpl_data,
                'browser_print_url': self.browser_print_url or 'https://localhost:9101',
                'device_name': self.browser_print_device or '',
                'printer_name': self.name,
            }
        }
