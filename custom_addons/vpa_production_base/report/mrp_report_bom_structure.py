# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import models


class ReportBomStructure(models.AbstractModel):
    """Extend BOM structure report to handle template lines (lines without products)."""
    _inherit = 'report.mrp.report_bom_structure'

    def _get_component_data(self, parent_bom, product, warehouse, bom_line, line_quantity, level, index, product_info, ignore_stock=False):
        """Override to skip template lines.

        Template lines (lines with category but no product) should not appear
        in cost calculations or BOM structure reports.
        """
        # Skip template lines (no product_id) - return None to skip this line
        if not bom_line.product_id:
            return None

        # For normal lines with products, use the standard logic
        return super()._get_component_data(
            parent_bom, product, warehouse, bom_line, line_quantity,
            level, index, product_info, ignore_stock
        )
