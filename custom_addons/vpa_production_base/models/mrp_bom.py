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
    # REVISION CONTROL
    # =========================================================================
    revision = fields.Char(
        string='Revision',
        default='1.0',
        copy=False,
        help="BOM revision number (e.g., 1.0, 2.0, 3.0)",
    )
    revision_history = fields.Text(
        string='Revision History',
        readonly=True,
        copy=False,
        help="History of all BOM revisions with dates and users",
    )
    code_with_revision = fields.Char(
        string='Reference with Revision',
        compute='_compute_code_with_revision',
        store=False,
        help="BOM code with revision number (e.g., JAZAM-DC-POOF (Rev 3.0))",
    )

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

    @api.depends('code', 'revision')
    def _compute_code_with_revision(self):
        """Compute BOM code with revision number."""
        import re
        for bom in self:
            if bom.code:
                # Clean the code by removing Odoo's automatic "(new) X" suffix
                clean_code = re.sub(r'\s*\(new\)\s*\d*', '', bom.code).strip()
                if bom.revision:
                    bom.code_with_revision = f"{clean_code} (Rev {bom.revision})"
                else:
                    bom.code_with_revision = clean_code
            else:
                bom.code_with_revision = False

    @api.depends('code', 'revision', 'product_tmpl_id')
    def _compute_display_name(self):
        """Override display name to use cleaned code with revision."""
        import re
        for bom in self:
            if bom.code:
                # Clean the code by removing Odoo's automatic "(new) X" suffix
                clean_code = re.sub(r'\s*\(new\)\s*\d*', '', bom.code).strip()
                if bom.revision:
                    bom.display_name = f"{clean_code} (Rev {bom.revision})"
                else:
                    bom.display_name = clean_code
            elif bom.product_tmpl_id:
                bom.display_name = bom.product_tmpl_id.display_name
            else:
                bom.display_name = _("Bill of Materials")

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
            vals.setdefault('revision', '1.0')
            # Initialize revision history
            revision = vals.get('revision', '1.0')
            user = self.env.user.name
            date = fields.Datetime.now().strftime('%Y-%m-%d %H:%M')
            vals['revision_history'] = f"Rev {revision} - {date} by {user}\n"
        return super().create(vals_list)

    def action_create_new_revision(self):
        """Create a new revision of this BOM."""
        self.ensure_one()

        # Parse current revision (e.g., "1.0" -> 1.0)
        try:
            current_rev = float(self.revision or '1.0')
            new_rev = f"{int(current_rev) + 1}.0"
        except (ValueError, TypeError):
            new_rev = "2.0"

        # Update revision history
        user = self.env.user.name
        date = fields.Datetime.now().strftime('%Y-%m-%d %H:%M')
        history_line = f"Rev {new_rev} - {date} by {user}\n"

        self.write({
            'revision': new_rev,
            'revision_history': (self.revision_history or '') + history_line,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('New Revision Created'),
                'message': _('BOM updated to revision %s') % new_rev,
                'type': 'success',
                'sticky': False,
            }
        }
