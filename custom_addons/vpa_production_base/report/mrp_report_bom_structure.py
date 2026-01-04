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
        """Override to filter template lines and fix reference display."""
        # Filter out template lines before processing
        original_lines = bom.bom_line_ids
        bom.bom_line_ids = original_lines.filtered(lambda l: l.product_id)

        try:
            # Call parent with filtered lines
            result = super()._get_bom_data(bom, warehouse, product, line_qty, level)

            # Fix the 'code' field in the result dictionary to show revision
            if result and 'code' in result and hasattr(bom, 'code_with_revision') and bom.code_with_revision:
                result['code'] = bom.code_with_revision

            return result
        finally:
            # Always restore original lines
            bom.bom_line_ids = original_lines
