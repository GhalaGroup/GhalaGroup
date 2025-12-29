# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

import json
import base64
import logging
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class UomConversionBackup(models.Model):
    """Model to handle backup and restore of UoM conversions"""
    _name = 'uom.conversion.backup'
    _description = 'UoM Conversion Backup'
    _order = 'create_date desc'

    name = fields.Char(string='Backup Name', required=True)
    backup_date = fields.Datetime(string='Backup Date', default=fields.Datetime.now)
    backup_type = fields.Selection([
        ('manual', 'Manual Export'),
        ('auto_uninstall', 'Auto (Before Uninstall)'),
    ], string='Backup Type', default='manual')
    backup_data = fields.Text(string='Backup Data (JSON)')
    company_id = fields.Many2one('res.company', string='Company')
    conversion_count = fields.Integer(string='Conversions', compute='_compute_counts')
    product_count = fields.Integer(string='Products', compute='_compute_counts')
    is_restored = fields.Boolean(string='Restored', default=False)
    restored_date = fields.Datetime(string='Restored Date')
    restored_by_id = fields.Many2one('res.users', string='Restored By')
    notes = fields.Text(string='Notes')

    @api.depends('backup_data')
    def _compute_counts(self):
        for record in self:
            if record.backup_data:
                try:
                    data = json.loads(record.backup_data)
                    conversions = data.get('conversions', [])
                    record.conversion_count = len(conversions)
                    record.product_count = len(set(c.get('product_default_code') or c.get('product_name') for c in conversions))
                except Exception:
                    record.conversion_count = 0
                    record.product_count = 0
            else:
                record.conversion_count = 0
                record.product_count = 0

    @api.model
    def export_all_conversions(self, company_id=None, backup_type='manual'):
        """Export all UoM conversions to JSON and create backup record"""
        backup_data = self._get_export_data(company_id)

        if not backup_data['conversions']:
            _logger.info("No UoM conversions to backup")
            return False

        company_name = ''
        if company_id:
            company = self.env['res.company'].browse(company_id)
            company_name = f" - {company.name}"

        backup = self.create({
            'name': f"UoM Conversion Backup{company_name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            'backup_type': backup_type,
            'backup_data': json.dumps(backup_data, indent=2, default=str),
            'company_id': company_id,
        })

        _logger.info(f"Created UoM conversion backup: {backup.name} with {len(backup_data['conversions'])} conversions")
        return backup

    @api.model
    def _get_export_data(self, company_id=None):
        """Get all UoM conversions as dictionary"""
        domain = []
        if company_id:
            domain = [('company_id', '=', company_id)]

        conversions = []
        conversion_records = self.env['product.uom.conversion'].search(domain)

        for conv in conversion_records:
            conversions.append({
                # Product identification (multiple ways to find product)
                'product_tmpl_id': conv.product_tmpl_id.id,
                'product_name': conv.product_tmpl_id.name,
                'product_default_code': conv.product_tmpl_id.default_code,
                # UoM identification
                'uom_id': conv.uom_id.id,
                'uom_name': conv.uom_id.name,
                'base_uom_id': conv.base_uom_id.id,
                'base_uom_name': conv.base_uom_id.name,
                # Conversion values
                'alt_qty': conv.alt_qty,
                'base_qty': conv.base_qty,
                'name': conv.name,
                'rounding': conv.rounding,
                'sequence': conv.sequence,
                'active': conv.active,
                # Company
                'company_id': conv.company_id.id if conv.company_id else None,
                'company_name': conv.company_id.name if conv.company_id else None,
            })

        return {
            'version': '19.0.1.0.0',
            'module': 'vpa_uom',
            'export_date': datetime.now().isoformat(),
            'conversions': conversions,
        }

    def action_restore(self):
        """Restore UoM conversions from this backup"""
        self.ensure_one()

        if not self.backup_data:
            raise UserError(_("No backup data found"))

        try:
            data = json.loads(self.backup_data)
        except json.JSONDecodeError:
            raise UserError(_("Invalid backup data format"))

        restored_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        Conversion = self.env['product.uom.conversion']

        for conv_data in data.get('conversions', []):
            try:
                # Find product by default_code first, then by name
                product = self._find_product(conv_data)
                if not product:
                    errors.append(_("Product not found: %s (code: %s)") % (
                        conv_data.get('product_name'),
                        conv_data.get('product_default_code')
                    ))
                    continue

                # Find UoM by name
                uom = self._find_uom(conv_data.get('uom_id'), conv_data.get('uom_name'))
                if not uom:
                    errors.append(_("UoM not found: %s") % conv_data.get('uom_name'))
                    continue

                # Check if conversion already exists
                existing = Conversion.search([
                    ('product_tmpl_id', '=', product.id),
                    ('uom_id', '=', uom.id),
                ], limit=1)

                vals = {
                    'product_tmpl_id': product.id,
                    'uom_id': uom.id,
                    'alt_qty': conv_data.get('alt_qty', 1.0),
                    'base_qty': conv_data.get('base_qty', 1.0),
                    'name': conv_data.get('name'),
                    'rounding': conv_data.get('rounding', 0.01),
                    'sequence': conv_data.get('sequence', 10),
                    'active': conv_data.get('active', True),
                }

                if existing:
                    existing.write(vals)
                    updated_count += 1
                    _logger.info(f"Updated conversion: {product.name} - {uom.name}")
                else:
                    Conversion.create(vals)
                    restored_count += 1
                    _logger.info(f"Created conversion: {product.name} - {uom.name}")

            except Exception as e:
                errors.append(_("Error restoring %s: %s") % (
                    conv_data.get('product_name', 'Unknown'),
                    str(e)
                ))

        # Mark as restored
        self.write({
            'is_restored': True,
            'restored_date': fields.Datetime.now(),
            'restored_by_id': self.env.uid,
        })

        # Prepare message
        message = _('Restore completed:\n- Created: %d conversions\n- Updated: %d conversions') % (
            restored_count, updated_count
        )
        if errors:
            message += _('\n\nErrors (%d):') % len(errors)
            message += '\n' + '\n'.join(errors[:10])
            if len(errors) > 10:
                message += _('\n... and %d more errors') % (len(errors) - 10)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Restore Complete'),
                'message': message,
                'type': 'success' if not errors else 'warning',
                'sticky': True,
            }
        }

    def _find_product(self, conv_data):
        """Find product template by ID, default_code, or name"""
        Product = self.env['product.template']

        # Try by ID first
        product = Product.browse(conv_data.get('product_tmpl_id')).exists()
        if product:
            return product

        # Try by default_code
        if conv_data.get('product_default_code'):
            product = Product.search([
                ('default_code', '=', conv_data['product_default_code'])
            ], limit=1)
            if product:
                return product

        # Try by name
        if conv_data.get('product_name'):
            product = Product.search([
                ('name', '=', conv_data['product_name'])
            ], limit=1)
            if product:
                return product

        return False

    def _find_uom(self, uom_id, uom_name):
        """Find UoM by ID or name"""
        Uom = self.env['uom.uom']

        # Try by ID first
        uom = Uom.browse(uom_id).exists()
        if uom:
            return uom

        # Try by name
        if uom_name:
            uom = Uom.search([('name', '=', uom_name)], limit=1)
            if uom:
                return uom

        return False

    def action_download_json(self):
        """Download backup as JSON file"""
        self.ensure_one()

        if not self.backup_data:
            raise UserError(_("No backup data found"))

        # Create filename
        company_part = self.company_id.name if self.company_id else "All Companies"
        date_part = self.backup_date.strftime('%Y-%m-%d')
        filename = f"VPA UoM Conversion Backup - {company_part} ({date_part}).json"

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(self.backup_data.encode('utf-8')),
            'mimetype': 'application/json',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    @api.model
    def restore_from_latest_backup(self):
        """Restore from the most recent auto backup if exists.

        This is called when the module is reinstalled to recover data
        that was backed up before uninstall.
        """
        latest_backup = self.search([
            ('backup_type', '=', 'auto_uninstall'),
            ('is_restored', '=', False),
        ], order='create_date desc', limit=1)

        if latest_backup:
            _logger.info(f"Found auto backup from {latest_backup.backup_date}, restoring...")
            latest_backup.action_restore()
            return True
        return False

    @api.model
    def create_auto_backup(self):
        """Create automatic backup before module uninstall.

        This should be called from pre_uninstall hook.
        """
        try:
            backup = self.export_all_conversions(backup_type='auto_uninstall')
            if backup:
                _logger.info(f"Auto backup created: {backup.name}")
                return True
        except Exception as e:
            _logger.error(f"Failed to create auto backup: {e}")
        return False


class UomConversionBackupWizard(models.TransientModel):
    """Wizard for backup/restore operations"""
    _name = 'uom.conversion.backup.wizard'
    _description = 'UoM Conversion Backup Wizard'

    action_type = fields.Selection([
        ('export', 'Export Conversions'),
        ('import', 'Import from File'),
    ], string='Action', default='export', required=True)

    company_id = fields.Many2one(
        'res.company', string='Company',
        help='Leave empty to export all companies'
    )

    import_file = fields.Binary(string='Import File')
    import_filename = fields.Char(string='Filename')

    def action_execute(self):
        """Execute the selected action"""
        self.ensure_one()

        if self.action_type == 'export':
            backup = self.env['uom.conversion.backup'].export_all_conversions(
                company_id=self.company_id.id if self.company_id else None,
                backup_type='manual'
            )
            if backup:
                return backup.action_download_json()
            else:
                raise UserError(_("No conversions found to export"))

        elif self.action_type == 'import':
            if not self.import_file:
                raise UserError(_("Please select a file to import"))

            try:
                file_content = base64.b64decode(self.import_file).decode('utf-8')
                data = json.loads(file_content)
            except Exception as e:
                raise UserError(_("Invalid file format: %s") % str(e))

            # Validate format
            if 'conversions' not in data:
                raise UserError(_("Invalid backup file: missing 'conversions' key"))

            # Create a backup record with the imported data
            backup = self.env['uom.conversion.backup'].create({
                'name': f"Import - {self.import_filename or 'Unknown'}",
                'backup_type': 'manual',
                'backup_data': json.dumps(data, indent=2),
            })

            return backup.action_restore()
