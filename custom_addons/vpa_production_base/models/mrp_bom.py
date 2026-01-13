# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class MrpBom(models.Model):
    """Extend mrp.bom with audit trail and BOM Manager restrictions."""
    _inherit = ['mrp.bom', 'mail.thread', 'mail.activity.mixin']
    _name = 'mrp.bom'
    # Sort Master BOMs first (is_master_bom DESC), then by sequence and id
    _order = 'is_master_bom desc, sequence, id'

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
    # MASTER BOM STATUS & CONVERSION TRACKING
    # =========================================================================
    master_bom_status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('pending', 'Pending Review'),
            ('active', 'Active'),
        ],
        string='Master BOM Status',
        default='active',
        tracking=True,
        copy=False,
        help="Status of the Master BOM:\n"
             "- Draft: Work in progress\n"
             "- Pending Review: Converted from standard BOM, needs category assignment\n"
             "- Active: Ready for use in Manufacturing Orders",
    )
    source_bom_id = fields.Many2one(
        'mrp.bom',
        string='Source BOM',
        readonly=True,
        copy=False,
        help="Original BOM this Master BOM was converted from",
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
    can_convert_to_master = fields.Boolean(
        compute='_compute_can_convert_to_master',
        help="Technical field to show/hide Convert to Master BOM button",
    )

    @api.depends('bom_line_ids', 'bom_line_ids.bom_category_id', 'bom_line_ids.product_id')
    def _compute_is_master_bom(self):
        """A Master BOM has at least one line with category but no product."""
        for bom in self:
            bom.is_master_bom = any(
                line.bom_category_id and not line.product_id
                for line in bom.bom_line_ids
            )

    @api.depends('is_master_bom', 'bom_line_ids', 'bom_line_ids.product_id')
    def _compute_can_convert_to_master(self):
        """Can convert if: not already a Master BOM and has product lines."""
        for bom in self:
            bom.can_convert_to_master = (
                not bom.is_master_bom
                and bool(bom.bom_line_ids.filtered(lambda l: l.product_id and not l.display_type))
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

    @api.depends('code', 'revision', 'product_tmpl_id', 'is_master_bom', 'master_bom_status')
    def _compute_display_name(self):
        """Override display name to use cleaned code with revision and Master BOM indicator."""
        import re
        for bom in self:
            if bom.code:
                # Clean the code by removing Odoo's automatic "(new) X" suffix
                clean_code = re.sub(r'\s*\(new\)\s*\d*', '', bom.code).strip()
                if bom.revision:
                    name = f"{clean_code} (Rev {bom.revision})"
                else:
                    name = clean_code
                # Add Master BOM indicator if this is a Master BOM
                if bom.is_master_bom:
                    bom.display_name = f"⭐ {name} [Master BOM]"
                else:
                    bom.display_name = name
            elif bom.product_tmpl_id:
                name = bom.product_tmpl_id.display_name
                if bom.is_master_bom:
                    bom.display_name = f"⭐ {name} [Master BOM]"
                else:
                    bom.display_name = name
            else:
                bom.display_name = _("Bill of Materials")

            # Add pending indicator for Master BOMs awaiting review
            if bom.is_master_bom and bom.master_bom_status == 'pending':
                bom.display_name = f"[PENDING] {bom.display_name}"

    # =========================================================================
    # OVERRIDES
    # =========================================================================
    def write(self, vals):
        """Track modifications in audit fields and clean code field."""
        vals['last_modified_by_id'] = self.env.user.id
        vals['last_modified_date'] = fields.Datetime.now()

        # Clean the code field if it contains "(new)" suffix
        if 'code' in vals and vals['code']:
            import re
            vals['code'] = re.sub(r'\s*\(new\)\s*\d*', '', vals['code']).strip()

        result = super().write(vals)

        # Force recompute display_name after code changes
        if 'code' in vals or 'revision' in vals:
            self._compute_display_name()

        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure created_by and created_date are set and clean code field."""
        import re
        for vals in vals_list:
            vals.setdefault('created_by_id', self.env.user.id)
            vals.setdefault('created_date', fields.Datetime.now())
            vals.setdefault('revision', '1.0')

            # Clean the code field if it contains "(new)" suffix
            if 'code' in vals and vals['code']:
                vals['code'] = re.sub(r'\s*\(new\)\s*\d*', '', vals['code']).strip()

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

    # =========================================================================
    # MASTER BOM CONVERSION
    # =========================================================================
    def action_convert_to_master_bom(self):
        """Convert this BOM to a Master BOM (creates a copy).

        Creates a copy of the BOM with:
        - Status set to 'pending'
        - Each line's product stored in original_product_id
        - product_id cleared (making it a template line)
        - Code suffixed with '-MASTER'
        - Revision reset to '1.0'
        - Conversion logged in revision_history
        """
        self.ensure_one()

        if self.is_master_bom:
            from odoo.exceptions import UserError
            raise UserError(_("This BOM is already a Master BOM."))

        product_lines = self.bom_line_ids.filtered(lambda l: l.product_id and not l.display_type)
        if not product_lines:
            from odoo.exceptions import UserError
            raise UserError(_("Cannot convert: BOM has no product lines."))

        # Prepare new BOM values
        new_code = f"{self.code}-MASTER" if self.code else False
        user = self.env.user.name
        date = fields.Datetime.now().strftime('%Y-%m-%d %H:%M')

        # Copy BOM
        new_bom = self.copy({
            'code': new_code,
            'master_bom_status': 'pending',
            'source_bom_id': self.id,
            'revision': '1.0',
            'revision_history': f"Rev 1.0 - {date} by {user}\n  Converted from: {self.display_name}\n",
        })

        # Convert lines: store product in original_product_id, clear product_id
        for line in new_bom.bom_line_ids:
            if line.product_id and not line.display_type:
                # Get category from line or from product
                category = line.bom_category_id or line.product_id.product_tmpl_id.bom_category_id
                line.write({
                    'original_product_id': line.product_id.id,
                    'bom_category_id': category.id if category else False,
                    'product_id': False,
                })

        # Open the new Master BOM
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom',
            'res_id': new_bom.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'},
        }

    def action_activate_master_bom(self):
        """Activate the Master BOM after review.

        Validates that all template lines have a bom_category_id assigned.
        """
        self.ensure_one()

        if self.master_bom_status != 'pending':
            from odoo.exceptions import UserError
            raise UserError(_("Only pending Master BOMs can be activated."))

        # Validation: All lines must have a category (except sections/notes)
        lines_without_category = self.bom_line_ids.filtered(
            lambda l: not l.product_id and not l.bom_category_id and not l.display_type
        )
        if lines_without_category:
            from odoo.exceptions import ValidationError
            raise ValidationError(_(
                "Cannot activate: %d line(s) have no BOM Category assigned.\n"
                "Please assign a category to all template lines before activating."
            ) % len(lines_without_category))

        user = self.env.user.name
        date = fields.Datetime.now().strftime('%Y-%m-%d %H:%M')

        self.write({
            'master_bom_status': 'active',
            'revision_history': (self.revision_history or '') + f"  Activated: {date} by {user}\n",
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Master BOM Activated'),
                'message': _('Master BOM %s is now active and ready for use.') % self.display_name,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_set_draft(self):
        """Set Master BOM back to draft status."""
        self.ensure_one()
        self.write({'master_bom_status': 'draft'})
