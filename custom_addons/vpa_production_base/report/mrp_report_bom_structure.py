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
        # Create a wrapper BOM object with filtered lines
        class FilteredBom:
            def __init__(self, original_bom):
                self._bom = original_bom
                # Filter out template lines (lines without product_id)
                self.bom_line_ids = original_bom.bom_line_ids.filtered(lambda l: l.product_id)

            def __getattr__(self, name):
                # Use code_with_revision for 'code' field to show revision in report
                if name == 'code' and hasattr(self._bom, 'code_with_revision'):
                    return self._bom.code_with_revision or self._bom.code
                # Delegate all other attributes to original BOM
                return getattr(self._bom, name)

        # Use filtered BOM for the report
        filtered_bom = FilteredBom(bom)

        # Call parent with filtered BOM
        result = super()._get_bom_data(filtered_bom, warehouse, product, line_qty, level)

        # Also fix the 'code' field in the result dictionary
        if result and 'code' in result and bom.code_with_revision:
            result['code'] = bom.code_with_revision

        return result
