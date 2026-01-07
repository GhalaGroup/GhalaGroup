# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class MrpBom(models.Model):
    """Extend mrp.bom with Product Category field for Master BOMs filtering."""
    _inherit = 'mrp.bom'

    # =========================================================================
    # RELATED FIELDS (for search panel filtering in Master BOMs view)
    # =========================================================================
    product_categ_id = fields.Many2one(
        'product.category',
        string='Product Category',
        related='product_tmpl_id.categ_id',
        store=True,
        readonly=True,
        help="Product category of the BOM's product (for filtering in Master BOMs view)",
    )
