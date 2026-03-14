# -*- coding: utf-8 -*-
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_default_vpa_report(self, document_type):
        """Get the default VPA report action for this document type"""
        # Search for VPA template marked as default for this document type and company
        vpa_template = self.env['vpa.document.template'].search([
            ('company_id', '=', self.company_id.id),
            ('document_type', '=', document_type),
            ('is_default_print', '=', True),
            ('active', '=', True),
        ], limit=1)

        if vpa_template and vpa_template.report_action_id:
            _logger.info(f"Found default VPA template: {vpa_template.name} for document type: {document_type}")
            return vpa_template.report_action_id

        return None

    def action_quotation_send(self):
        """Override to use VPA template if set as default for email"""
        # Check if there's a default email template
        vpa_template = self.env['vpa.document.template'].search([
            ('company_id', '=', self.company_id.id),
            ('document_type', '=', 'quotation'),
            ('is_default_email', '=', True),
            ('active', '=', True),
        ], limit=1)

        # Call parent method to get the compose wizard
        result = super(SaleOrder, self).action_quotation_send()

        # If VPA template is set as default for email, inject its report
        if vpa_template and vpa_template.report_action_id:
            _logger.info(f"Using VPA template for email: {vpa_template.name}")
            # Update the report to use in email
            if result.get('context'):
                result['context']['default_report_template_ids'] = [(4, vpa_template.report_action_id.id)]

        return result

    def _get_line_mo_map(self):
        """Build a mapping of sale.order.line ID -> mrp.production recordset.

        Used by the Production Summary report to show correct MOs per line.
        First tries sale_line_id (direct link), then falls back to creation-order matching.
        """
        self.ensure_one()
        MrpProduction = self.env['mrp.production']
        all_mos = self.mrp_production_ids.sorted('id')
        line_mo_map = {}
        used_mo_ids = set()

        # First pass: MOs with sale_line_id
        for mo in all_mos:
            if mo.sale_line_id:
                key = mo.sale_line_id.id
                if key in line_mo_map:
                    line_mo_map[key] |= mo
                else:
                    line_mo_map[key] = mo
                used_mo_ids.add(mo.id)

        # Second pass: unlinked MOs matched by creation order
        unlinked_mos = [m for m in all_mos if m.id not in used_mo_ids]
        product_lines = [
            l for l in self.order_line
            if l.product_uom_qty > 0 and not l.display_type and l.id not in line_mo_map
        ]
        for idx, pl in enumerate(product_lines):
            if idx < len(unlinked_mos):
                line_mo_map[pl.id] = unlinked_mos[idx]

        return line_mo_map
