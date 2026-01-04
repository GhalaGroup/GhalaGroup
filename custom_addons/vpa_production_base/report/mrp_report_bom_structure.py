# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import models


class MrpBomLine(models.Model):
    """Extend mrp.bom.line to mark template lines."""
    _inherit = 'mrp.bom.line'

    def _skip_bom_line(self, product):
        """Override to skip template lines in BOM reports.

        Template lines (lines with category but no product) should not appear
        in cost calculations or BOM structure reports.
        """
        # Skip template lines (no product_id)
        if not self.product_id:
            return True

        # Use parent logic for other checks
        return super()._skip_bom_line(product)
