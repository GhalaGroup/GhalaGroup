# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ImportFooterWizard(models.TransientModel):
    _name = 'vpa.import.footer.wizard'
    _description = 'Import Footer Data Wizard'

    template_id = fields.Many2one(
        'vpa.document.template',
        string='Current Template',
        required=True,
        readonly=True,
    )

    source_template_id = fields.Many2one(
        'vpa.document.template',
        string='Import From Template',
        required=True,
        domain="[('company_id', '=', company_id), ('active', '=', True), ('id', '!=', template_id), ('footer_enabled', '=', True)]",
        help='Select a template to import footer data from'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='template_id.company_id',
        readonly=True,
    )

    def action_import(self):
        """Import footer data from source template to current template"""
        self.ensure_one()

        source = self.source_template_id
        target = self.template_id

        # Import footer settings from source template
        target.write({
            'footer_layout': source.footer_layout,
            'footer_show_shape': source.footer_show_shape,
            'footer_shape_opacity': source.footer_shape_opacity,
            'footer_bank_details_show': source.footer_bank_details_show,
            'footer_column_1_title': source.footer_column_1_title,
            'footer_column_1_content': source.footer_column_1_content,
            'footer_column_2_title': source.footer_column_2_title,
            'footer_column_2_content': source.footer_column_2_content,
            'footer_column_3_title': source.footer_column_3_title,
            'footer_column_3_content': source.footer_column_3_content,
            'footer_show_page_number': source.footer_show_page_number,
            'footer_page_number_format': source.footer_page_number_format,
            'footer_message_type': source.footer_message_type,
            'footer_custom_message': source.footer_custom_message,
            'footer_show_content': source.footer_show_content,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Footer Data Imported'),
                'message': _('Footer data from "%s" has been imported successfully. Please save the template to keep these changes.') % source.name,
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window_close',
                }
            }
        }
