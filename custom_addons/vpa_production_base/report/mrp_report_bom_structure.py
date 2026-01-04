# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, models


class MrpBom(models.Model):
    """Extend mrp.bom to filter out template lines for reports."""
    _inherit = 'mrp.bom'

    @api.depends('bom_line_ids.product_id')
    def _compute_bom_line_ids(self):
        """Override to provide filtered lines for reports."""
        # This is called by various places, no actual compute needed
        pass

    def _get_report_lines(self):
        """Return only BOM lines that have products (exclude template lines).

        Template lines (category but no product) are used during manufacturing
        for worker selection, but should not appear in cost reports.
        """
        return self.bom_line_ids.filtered(lambda line: line.product_id)


class ReportBomStructure(models.AbstractModel):
    """Extend BOM structure report to handle template lines (lines without products).

    Template lines have bom_category_id but no product_id, which causes the standard
    report to fail when trying to calculate costs. This extension filters out template
    lines before processing.
    """
    _inherit = 'report.mrp.report_bom_structure'

    def _get_bom_data(self, bom, warehouse, product=False, line_qty=False, level=0):
        """Override to use only lines with products.

        We temporarily replace bom_line_ids with filtered lines that have products,
        call the parent method, then restore the original lines.
        """
        # Store original lines
        original_lines = bom.bom_line_ids

        # Temporarily replace with filtered lines (only lines with products)
        filtered_lines = original_lines.filtered(lambda line: line.product_id)

        # Use ORM's recordset assignment to temporarily modify
        bom.bom_line_ids = filtered_lines

        try:
            # Call parent with filtered lines
            result = super()._get_bom_data(bom, warehouse, product, line_qty, level)
        finally:
            # Restore original lines
            bom.bom_line_ids = original_lines

        return result
