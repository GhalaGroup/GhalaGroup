# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import models


class ReportBomStructure(models.AbstractModel):
    """Extend BOM structure report to handle template lines (lines without products).

    Template lines have bom_category_id but no product_id, which causes the standard
    report to fail when trying to calculate costs. This extension filters out template
    lines from the component data generation.
    """
    _inherit = 'report.mrp.report_bom_structure'

    def _get_bom_data(self, bom, warehouse, product=False, line_qty=False, level=0):
        """Override to filter out template lines before processing."""
        # Get the original data
        result = super()._get_bom_data(bom, warehouse, product, line_qty, level)

        # Filter components to remove template lines (lines without product_id)
        if result and 'components' in result:
            result['components'] = [
                comp for comp in result['components']
                if comp.get('line') and comp['line'].product_id
            ]

        return result

    def _get_component_data(self, parent_bom, product, warehouse, bom_line, line_quantity, level, index, product_info, ignore_stock=False):
        """Override to skip template lines entirely.

        Template lines don't have a product_id, so we can't calculate their cost
        or display them in the BOM structure report. Workers will select the actual
        product during manufacturing.
        """
        # Skip template lines (lines with category but no product)
        if not bom_line.product_id:
            return {}

        # For normal lines with products, use the standard logic
        return super()._get_component_data(
            parent_bom, product, warehouse, bom_line, line_quantity,
            level, index, product_info, ignore_stock
        )
