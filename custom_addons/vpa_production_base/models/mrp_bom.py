# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class MrpBom(models.Model):
    """Extend mrp.bom with audit trail and BOM Manager restrictions."""
    _inherit = ['mrp.bom', 'mail.thread', 'mail.activity.mixin']
    _name = 'mrp.bom'

    # =========================================================================
    # AUDIT TRAIL FIELDS
    # =========================================================================
    created_by_id = fields.Many2one(
        'res.users',
        string='Created By',
        readonly=True,
        default=lambda self: self.env.user,
        copy=False,
        help="User who created this BOM",
    )
    created_date = fields.Datetime(
        string='Created Date',
        readonly=True,
        default=fields.Datetime.now,
        copy=False,
        help="Date and time when this BOM was created",
    )
    last_modified_by_id = fields.Many2one(
        'res.users',
        string='Last Modified By',
        readonly=True,
        copy=False,
        help="User who last modified this BOM",
    )
    last_modified_date = fields.Datetime(
        string='Last Modified Date',
        readonly=True,
        copy=False,
        help="Date and time of last modification",
    )

    # =========================================================================
    # TRACKING FIELDS (for chatter history)
    # =========================================================================
    # Override fields to add tracking
    product_tmpl_id = fields.Many2one(tracking=True)
    product_qty = fields.Float(tracking=True)
    product_uom_id = fields.Many2one(tracking=True)
    code = fields.Char(tracking=True)
    type = fields.Selection(tracking=True)
    active = fields.Boolean(tracking=True)

    # =========================================================================
    # COMPUTED FIELDS
    # =========================================================================
    is_master_bom = fields.Boolean(
        string='Is Master BOM',
        compute='_compute_is_master_bom',
        store=True,
        help="True if this BOM has template lines (with categories, no specific products)",
    )

    @api.depends('bom_line_ids', 'bom_line_ids.bom_category_id', 'bom_line_ids.product_id')
    def _compute_is_master_bom(self):
        """A Master BOM has at least one line with category but no product."""
        for bom in self:
            bom.is_master_bom = any(
                line.bom_category_id and not line.product_id
                for line in bom.bom_line_ids
            )

    # =========================================================================
    # OVERRIDES
    # =========================================================================
    def write(self, vals):
        """Track modifications in audit fields."""
        vals['last_modified_by_id'] = self.env.user.id
        vals['last_modified_date'] = fields.Datetime.now()
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure created_by and created_date are set."""
        for vals in vals_list:
            vals.setdefault('created_by_id', self.env.user.id)
            vals.setdefault('created_date', fields.Datetime.now())
        return super().create(vals_list)
