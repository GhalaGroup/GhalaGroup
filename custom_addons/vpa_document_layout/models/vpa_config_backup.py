# -*- coding: utf-8 -*-
import json
import base64
import logging
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class VPAConfigBackup(models.Model):
    _name = 'vpa.config.backup'
    _description = 'VPA Configuration Backup'
    _order = 'create_date desc'

    name = fields.Char(string='Backup Name', required=True)
    backup_date = fields.Datetime(string='Backup Date', default=fields.Datetime.now)
    backup_type = fields.Selection([
        ('manual', 'Manual Export'),
        ('auto_uninstall', 'Auto (Before Uninstall)'),
    ], string='Backup Type', default='manual')
    backup_data = fields.Text(string='Backup Data (JSON)')
    company_id = fields.Many2one('res.company', string='Company')
    template_count = fields.Integer(string='Templates', compute='_compute_counts')
    footer_count = fields.Integer(string='Footers', compute='_compute_counts')

    @api.depends('backup_data')
    def _compute_counts(self):
        for record in self:
            if record.backup_data:
                try:
                    data = json.loads(record.backup_data)
                    record.template_count = len(data.get('templates', []))
                    record.footer_count = len(data.get('footers', []))
                except Exception:
                    record.template_count = 0
                    record.footer_count = 0
            else:
                record.template_count = 0
                record.footer_count = 0

    @api.model
    def export_all_configs(self, company_id=None, backup_type='manual'):
        """Export all VPA configurations to JSON and create backup record"""
        backup_data = self._get_export_data(company_id)

        if not backup_data['templates'] and not backup_data['footers']:
            _logger.info("No VPA configurations to backup")
            return False

        company_name = ''
        if company_id:
            company = self.env['res.company'].browse(company_id)
            company_name = f" - {company.name}"

        backup = self.create({
            'name': f"VPA Backup{company_name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            'backup_type': backup_type,
            'backup_data': json.dumps(backup_data, indent=2, default=str),
            'company_id': company_id,
        })

        _logger.info(f"Created VPA backup: {backup.name} with {len(backup_data['templates'])} templates and {len(backup_data['footers'])} footers")
        return backup

    @api.model
    def _get_export_data(self, company_id=None):
        """Get all VPA configurations as dictionary"""
        domain = []
        if company_id:
            domain = [('company_id', '=', company_id)]

        # Export templates
        templates = []
        template_records = self.env['vpa.document.template'].search(domain)
        for tmpl in template_records:
            templates.append({
                'name': tmpl.name,
                'company_id': tmpl.company_id.id,
                'company_name': tmpl.company_id.name,
                'active': tmpl.active,
                'sequence': tmpl.sequence,
                'target_app': tmpl.target_app,
                'document_type': tmpl.document_type,
                'print_name_pattern': tmpl.print_name_pattern,
                'print_name_expression': tmpl.print_name_expression,
                'hide_odoo_header': tmpl.hide_odoo_header,
                'hide_odoo_footer': tmpl.hide_odoo_footer,
                'header_logo_alignment': tmpl.header_logo_alignment,
                'header_logo_width': tmpl.header_logo_width,
                'header_logo_height': tmpl.header_logo_height,
                'header_logo_aspect_ratio': tmpl.header_logo_aspect_ratio,
                'header_show_circle': tmpl.header_show_circle,
                'header_circle_size': tmpl.header_circle_size,
                'header_circle_opacity': tmpl.header_circle_opacity,
                'header_company_info_alignment': tmpl.header_company_info_alignment,
                'header_company_details_html': tmpl.header_company_details_html,
                'header_company_info_color': tmpl.header_company_info_color,
                'primary_accent_color': tmpl.primary_accent_color,
                'secondary_accent_color': tmpl.secondary_accent_color,
                'table_style': tmpl.table_style,
                'table_header_bg_color': tmpl.table_header_bg_color,
                'table_header_text_color': tmpl.table_header_text_color,
                'table_border_color': tmpl.table_border_color,
                'table_row_alt_bg': tmpl.table_row_alt_bg,
                'paper_size': tmpl.paper_size,
                'paper_orientation': tmpl.paper_orientation,
                'footer_show_shape': tmpl.footer_show_shape,
                'footer_shape_opacity': tmpl.footer_shape_opacity,
                'footer_layout': tmpl.footer_layout,
                'footer_bank_details_show': tmpl.footer_bank_details_show,
                'footer_column_1_title': tmpl.footer_column_1_title,
                'footer_column_1_content': tmpl.footer_column_1_content,
                'footer_column_2_title': tmpl.footer_column_2_title,
                'footer_column_2_content': tmpl.footer_column_2_content,
                'footer_column_3_title': tmpl.footer_column_3_title,
                'footer_column_3_content': tmpl.footer_column_3_content,
                'footer_custom_html': tmpl.footer_custom_html,
                'is_default_print': tmpl.is_default_print,
                'is_default_email': tmpl.is_default_email,
            })

        # Export footer configs
        footers = []
        footer_records = self.env['vpa.footer.config'].search(domain)
        for footer in footer_records:
            footers.append({
                'name': footer.name,
                'company_id': footer.company_id.id,
                'company_name': footer.company_id.name,
                'active': footer.active,
                'sequence': footer.sequence,
                'footer_type': footer.footer_type,
                'is_default_customer': footer.is_default_customer,
                'is_default_internal': footer.is_default_internal,
                'footer_layout': footer.footer_layout,
                'show_border': footer.show_border,
                'border_color': footer.border_color,
                'show_shape': footer.show_shape,
                'shape_color': footer.shape_color,
                'shape_opacity': footer.shape_opacity,
                'text_color': footer.text_color,
                'font_size': footer.font_size,
                'show_bank_details': footer.show_bank_details,
                'show_page_numbers': footer.show_page_numbers,
                'show_company_footer': footer.show_company_footer,
                'computer_generated_note': footer.computer_generated_note,
                'column_1_title': footer.column_1_title,
                'column_1_content': footer.column_1_content,
                'column_2_title': footer.column_2_title,
                'column_2_content': footer.column_2_content,
                'column_3_title': footer.column_3_title,
                'column_3_content': footer.column_3_content,
                'custom_html': footer.custom_html,
            })

        return {
            'version': '19.0.1.0.2',
            'export_date': datetime.now().isoformat(),
            'templates': templates,
            'footers': footers,
        }

    def action_restore(self):
        """Restore configurations from this backup"""
        self.ensure_one()

        if not self.backup_data:
            raise UserError(_("No backup data found"))

        try:
            data = json.loads(self.backup_data)
        except json.JSONDecodeError:
            raise UserError(_("Invalid backup data format"))

        restored_templates = 0
        restored_footers = 0

        # Restore templates
        for tmpl_data in data.get('templates', []):
            # Find company by name if ID doesn't match
            company = self._find_company(tmpl_data.get('company_id'), tmpl_data.get('company_name'))
            if not company:
                _logger.warning(f"Company not found for template: {tmpl_data.get('name')}")
                continue

            # Check if template already exists
            existing = self.env['vpa.document.template'].search([
                ('name', '=', tmpl_data['name']),
                ('company_id', '=', company.id),
            ], limit=1)

            vals = self._prepare_template_vals(tmpl_data, company)

            if existing:
                existing.write(vals)
                _logger.info(f"Updated template: {tmpl_data['name']}")
            else:
                self.env['vpa.document.template'].create(vals)
                _logger.info(f"Created template: {tmpl_data['name']}")
            restored_templates += 1

        # Restore footers
        for footer_data in data.get('footers', []):
            company = self._find_company(footer_data.get('company_id'), footer_data.get('company_name'))
            if not company:
                _logger.warning(f"Company not found for footer: {footer_data.get('name')}")
                continue

            # Check if footer already exists
            existing = self.env['vpa.footer.config'].search([
                ('name', '=', footer_data['name']),
                ('company_id', '=', company.id),
            ], limit=1)

            vals = self._prepare_footer_vals(footer_data, company)

            if existing:
                existing.write(vals)
                _logger.info(f"Updated footer: {footer_data['name']}")
            else:
                self.env['vpa.footer.config'].create(vals)
                _logger.info(f"Created footer: {footer_data['name']}")
            restored_footers += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Restore Complete'),
                'message': _('Restored %d templates and %d footer configurations.') % (restored_templates, restored_footers),
                'type': 'success',
                'sticky': False,
            }
        }

    def _find_company(self, company_id, company_name):
        """Find company by ID or name"""
        company = self.env['res.company'].browse(company_id).exists()
        if not company and company_name:
            company = self.env['res.company'].search([('name', '=', company_name)], limit=1)
        return company

    def _prepare_template_vals(self, data, company):
        """Prepare values dict for template creation/update"""
        return {
            'name': data.get('name'),
            'company_id': company.id,
            'active': data.get('active', True),
            'sequence': data.get('sequence', 10),
            'target_app': data.get('target_app'),
            'document_type': data.get('document_type'),
            'print_name_pattern': data.get('print_name_pattern'),
            'print_name_expression': data.get('print_name_expression'),
            'hide_odoo_header': data.get('hide_odoo_header', True),
            'hide_odoo_footer': data.get('hide_odoo_footer', True),
            'header_logo_alignment': data.get('header_logo_alignment', 'right'),
            'header_logo_width': data.get('header_logo_width', 250),
            'header_logo_height': data.get('header_logo_height', 100),
            'header_logo_aspect_ratio': data.get('header_logo_aspect_ratio', 'auto'),
            'header_show_circle': data.get('header_show_circle', True),
            'header_circle_size': data.get('header_circle_size', 300),
            'header_circle_opacity': data.get('header_circle_opacity', 0.25),
            'header_company_info_alignment': data.get('header_company_info_alignment', 'right'),
            'header_company_details_html': data.get('header_company_details_html'),
            'header_company_info_color': data.get('header_company_info_color', '#555555'),
            'primary_accent_color': data.get('primary_accent_color', '#875a7b'),
            'secondary_accent_color': data.get('secondary_accent_color', '#21b799'),
            'table_style': data.get('table_style', 'modern_light'),
            'table_header_bg_color': data.get('table_header_bg_color'),
            'table_header_text_color': data.get('table_header_text_color'),
            'table_border_color': data.get('table_border_color'),
            'table_row_alt_bg': data.get('table_row_alt_bg'),
            'paper_size': data.get('paper_size', 'a4'),
            'paper_orientation': data.get('paper_orientation', 'portrait'),
            'footer_show_shape': data.get('footer_show_shape', True),
            'footer_shape_opacity': data.get('footer_shape_opacity', 0.1),
            'footer_layout': data.get('footer_layout', 'two_col'),
            'footer_bank_details_show': data.get('footer_bank_details_show', True),
            'footer_column_1_title': data.get('footer_column_1_title'),
            'footer_column_1_content': data.get('footer_column_1_content'),
            'footer_column_2_title': data.get('footer_column_2_title'),
            'footer_column_2_content': data.get('footer_column_2_content'),
            'footer_column_3_title': data.get('footer_column_3_title'),
            'footer_column_3_content': data.get('footer_column_3_content'),
            'footer_custom_html': data.get('footer_custom_html'),
            'is_default_print': data.get('is_default_print', False),
            'is_default_email': data.get('is_default_email', False),
        }

    def _prepare_footer_vals(self, data, company):
        """Prepare values dict for footer creation/update"""
        return {
            'name': data.get('name'),
            'company_id': company.id,
            'active': data.get('active', True),
            'sequence': data.get('sequence', 10),
            'footer_type': data.get('footer_type', 'customer'),
            'is_default_customer': data.get('is_default_customer', False),
            'is_default_internal': data.get('is_default_internal', False),
            'footer_layout': data.get('footer_layout', 'single'),
            'show_border': data.get('show_border', True),
            'border_color': data.get('border_color', '#dee2e6'),
            'show_shape': data.get('show_shape', False),
            'shape_color': data.get('shape_color', '#21b799'),
            'shape_opacity': data.get('shape_opacity', 0.1),
            'text_color': data.get('text_color', '#666666'),
            'font_size': data.get('font_size', '8pt'),
            'show_bank_details': data.get('show_bank_details', True),
            'show_page_numbers': data.get('show_page_numbers', True),
            'show_company_footer': data.get('show_company_footer', True),
            'computer_generated_note': data.get('computer_generated_note'),
            'column_1_title': data.get('column_1_title'),
            'column_1_content': data.get('column_1_content'),
            'column_2_title': data.get('column_2_title'),
            'column_2_content': data.get('column_2_content'),
            'column_3_title': data.get('column_3_title'),
            'column_3_content': data.get('column_3_content'),
            'custom_html': data.get('custom_html'),
        }

    def action_download_json(self):
        """Download backup as JSON file"""
        self.ensure_one()

        if not self.backup_data:
            raise UserError(_("No backup data found"))

        # Create attachment for download
        filename = f"vpa_backup_{self.backup_date.strftime('%Y%m%d_%H%M%S')}.json"
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
        """Restore from the most recent auto backup if exists"""
        latest_backup = self.search([
            ('backup_type', '=', 'auto_uninstall'),
        ], order='create_date desc', limit=1)

        if latest_backup:
            _logger.info(f"Found auto backup from {latest_backup.backup_date}, restoring...")
            latest_backup.action_restore()
            return True
        return False


class VPAConfigBackupWizard(models.TransientModel):
    _name = 'vpa.config.backup.wizard'
    _description = 'VPA Configuration Backup Wizard'

    action_type = fields.Selection([
        ('export', 'Export Configurations'),
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
            backup = self.env['vpa.config.backup'].export_all_configs(
                company_id=self.company_id.id if self.company_id else None,
                backup_type='manual'
            )
            if backup:
                return backup.action_download_json()
            else:
                raise UserError(_("No configurations found to export"))

        elif self.action_type == 'import':
            if not self.import_file:
                raise UserError(_("Please select a file to import"))

            try:
                file_content = base64.b64decode(self.import_file).decode('utf-8')
                data = json.loads(file_content)
            except Exception as e:
                raise UserError(_("Invalid file format: %s") % str(e))

            # Create a backup record with the imported data
            backup = self.env['vpa.config.backup'].create({
                'name': f"Import - {self.import_filename or 'Unknown'}",
                'backup_type': 'manual',
                'backup_data': json.dumps(data, indent=2),
            })

            return backup.action_restore()
