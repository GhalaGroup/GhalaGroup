# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, models


class MrpBomLine(models.Model):
    """Extend mrp.bom.line to skip template lines in reports."""
    _inherit = 'mrp.bom.line'

    @api.model
    def _skip_bom_line(self, product):
        """Check if this BOM line should be skipped.

        Override to skip template lines (lines without products) in reports.
        """
        # Skip template lines - they have category but no product
        if not self.product_id:
            return True

        # Check parent logic for other skip conditions
        return super()._skip_bom_line(product) if hasattr(super(), '_skip_bom_line') else False


class ReportBomStructure(models.AbstractModel):
    """Extend BOM structure report to handle template lines."""
    _inherit = 'report.mrp.report_bom_structure'

    def _get_bom_data(self, bom, warehouse, product=False, line_qty=False, level=0):
        """Override to handle template lines and fix reference display."""
        result = super()._get_bom_data(bom, warehouse, product, line_qty, level)

        # Fix the 'code' field in the result dictionary to show revision
        if result and 'code' in result and hasattr(bom, 'code_with_revision') and bom.code_with_revision:
            result['code'] = bom.code_with_revision

        return result

    def _get_bom_line_data(self, line, warehouse, level, index, product_info, ignore_stock=False):
        """Override to handle template lines (lines without products)."""
        # Check if this is a template line (has category but no product)
        if line.bom_category_id and not line.product_id:
            # Return custom data structure for template lines
            return {
                'index': index,
                'level': level,
                'name': line.bom_category_id.name,
                'type': 'template',  # Mark as template line
                'category_code': line.bom_category_id.code or '',
                'description': line.line_description or '',
                'quantity': line.product_qty,
                'uom_name': line.product_uom_id.name if line.product_uom_id else '',
                'prod_cost': 0.0,
                'bom_cost': 0.0,
                'route_name': '',
                'route_detail': _('To be selected during manufacturing'),
                'lead_time': False,
                'visible': True,
                'quantity_available': 0.0,
                'quantity_on_hand': 0.0,
                'producible_qty': 0.0,
                'availability_display': _('Template'),
                'availability_state': 'template',
                'components_available': True,
                'lines': [],  # Template lines have no sub-components
            }

        # For standard lines with products, use parent logic
        return super()._get_bom_line_data(line, warehouse, level, index, product_info, ignore_stock)
