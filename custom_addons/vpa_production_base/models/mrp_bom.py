# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


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
    revision_history_html = fields.Html(
        string='Revision History (Formatted)',
        compute='_compute_revision_history_html',
        sanitize=False,
        help="Formatted HTML version of revision history for display",
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
            ('inactive', 'Inactive'),
        ],
        string='Master BOM Status',
        default='active',
        tracking=True,
        copy=False,
        help="Status of the Master BOM:\n"
             "- Draft: Work in progress\n"
             "- Pending Review: Converted from standard BOM, needs category assignment\n"
             "- Active: Ready for use in Manufacturing Orders\n"
             "- Inactive: Deactivated/replaced by another Master BOM",
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
        """A Master BOM has at least one line with category but no product.

        When a BOM becomes a Master BOM (by adding template lines), auto-calculate
        the revision number based on existing Master BOMs for the same product.
        """
        for bom in self:
            has_template_line = any(
                line.bom_category_id and not line.product_id
                for line in bom.bom_line_ids
            )

            # Check if BOM is BECOMING a Master BOM by reading stored value from DB
            was_master = False
            if bom.id:
                self.env.cr.execute(
                    "SELECT is_master_bom, revision FROM mrp_bom WHERE id = %s",
                    (bom.id,)
                )
                result = self.env.cr.fetchone()
                if result:
                    was_master = result[0] or False
                    stored_revision = result[1] or '1.0'
                else:
                    stored_revision = '1.0'
            else:
                stored_revision = '1.0'

            bom.is_master_bom = has_template_line

            # Auto-increment revision when BOM BECOMES a Master BOM
            # Only if revision is still default "1.0" and BOM exists in DB
            if has_template_line and not was_master and bom.id and stored_revision == '1.0':
                # Determine next revision number by checking existing Master BOMs
                if bom.product_id:
                    existing_boms = self.search([
                        ('product_id', '=', bom.product_id.id),
                        ('is_master_bom', '=', True),
                        ('id', '!=', bom.id),
                    ])
                elif bom.product_tmpl_id:
                    existing_boms = self.search([
                        ('product_tmpl_id', '=', bom.product_tmpl_id.id),
                        ('product_id', '=', False),
                        ('is_master_bom', '=', True),
                        ('id', '!=', bom.id),
                    ])
                else:
                    existing_boms = self.env['mrp.bom']

                if existing_boms:
                    # Get the highest revision number and increment
                    max_revision = 0.0
                    for existing_bom in existing_boms:
                        try:
                            rev = float(existing_bom.revision)
                            if rev > max_revision:
                                max_revision = rev
                        except (ValueError, TypeError):
                            continue

                    next_revision = f"{max_revision + 1.0:.1f}"
                    # Use SQL to avoid recursion (write triggers compute again)
                    self.env.cr.execute(
                        "UPDATE mrp_bom SET revision = %s WHERE id = %s",
                        (next_revision, bom.id)
                    )
                    # Invalidate cache so the new revision is visible
                    bom.invalidate_recordset(['revision'])

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

    @api.depends('revision_history')
    def _compute_revision_history_html(self):
        """Convert plain text revision history to formatted HTML timeline.

        Uses theme-aware colors that work in both light and dark modes.
        """
        import re
        for bom in self:
            if not bom.revision_history:
                bom.revision_history_html = False
                continue

            # Group entries by revision
            revisions = []
            current_revision = None
            lines = bom.revision_history.strip().split('\n')

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Main revision line: "Rev X.X - YYYY-MM-DD HH:MM by User"
                rev_match = re.match(r'^Rev\s+(\d+\.\d+)\s*-\s*(.+?)\s+by\s+(.+)$', line)
                if rev_match:
                    if current_revision:
                        revisions.append(current_revision)
                    current_revision = {
                        'number': rev_match.group(1),
                        'date': rev_match.group(2),
                        'user': rev_match.group(3),
                        'actions': []
                    }
                elif current_revision:
                    current_revision['actions'].append(line)

            if current_revision:
                revisions.append(current_revision)

            # Build timeline HTML with theme-aware styles
            html = '''
            <div class="revision-history-container" style="padding: 8px 0;">
                <table style="width: 100%; border-collapse: collapse; border-spacing: 0;">
                    <thead>
                        <tr style="border-bottom: 1px solid var(--o-border-color, rgba(0,0,0,0.1));">
                            <th style="text-align: left; padding: 10px 12px; font-weight: 600; opacity: 0.7; width: 90px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Rev</th>
                            <th style="text-align: left; padding: 10px 12px; font-weight: 600; opacity: 0.7; width: 160px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Date</th>
                            <th style="text-align: left; padding: 10px 12px; font-weight: 600; opacity: 0.7; width: 140px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Author</th>
                            <th style="text-align: left; padding: 10px 12px; font-weight: 600; opacity: 0.7; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
            '''

            for i, rev in enumerate(revisions):
                # Format actions with theme-aware badges
                actions_html = ''
                for action in rev['actions']:
                    if action.startswith('Activated:'):
                        # Green badge - works in both themes
                        actions_html += f'<span style="display: inline-block; padding: 3px 10px; margin: 2px 4px 2px 0; background: rgba(40, 167, 69, 0.15); color: #28a745; border-radius: 12px; font-size: 11px; font-weight: 500;">✓ Activated</span>'
                    elif action.startswith('Deactivated:'):
                        # Red badge
                        actions_html += f'<span style="display: inline-block; padding: 3px 10px; margin: 2px 4px 2px 0; background: rgba(220, 53, 69, 0.15); color: #dc3545; border-radius: 12px; font-size: 11px; font-weight: 500;">✕ Deactivated</span>'
                    elif action.startswith('Converted from:'):
                        # Blue badge
                        actions_html += f'<span style="display: inline-block; padding: 3px 10px; margin: 2px 4px 2px 0; background: rgba(23, 162, 184, 0.15); color: #17a2b8; border-radius: 12px; font-size: 11px; font-weight: 500;">↳ Converted</span>'
                    else:
                        actions_html += f'<span style="display: inline-block; padding: 3px 10px; margin: 2px 4px 2px 0; opacity: 0.6; font-size: 11px;">{action}</span>'

                if not actions_html:
                    actions_html = '<span style="opacity: 0.5; font-style: italic; font-size: 11px;">Initial version</span>'

                # Row with subtle hover effect via border
                html += f'''
                        <tr style="border-bottom: 1px solid var(--o-border-color, rgba(0,0,0,0.05));">
                            <td style="padding: 12px; vertical-align: middle;">
                                <span style="display: inline-block; padding: 4px 10px; background: #714B67; color: white; border-radius: 4px; font-weight: 600; font-size: 12px; min-width: 36px; text-align: center;">
                                    {rev['number']}
                                </span>
                            </td>
                            <td style="padding: 12px; font-size: 13px; vertical-align: middle; opacity: 0.8;">{rev['date']}</td>
                            <td style="padding: 12px; font-size: 13px; vertical-align: middle;">
                                <span style="color: #714B67; font-weight: 500;">{rev['user']}</span>
                            </td>
                            <td style="padding: 12px; vertical-align: middle;">{actions_html}</td>
                        </tr>
                '''

            html += '''
                    </tbody>
                </table>
            </div>
            '''

            bom.revision_history_html = html

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
    # VALIDATION
    # =========================================================================
    def _check_unique_revision(self):
        """Validate that revision is unique for Master BOMs of the same product."""
        for bom in self:
            if not bom.is_master_bom or not bom.revision:
                continue

            # Build domain to find other Master BOMs with same revision
            domain = [
                ('is_master_bom', '=', True),
                ('revision', '=', bom.revision),
                ('id', '!=', bom.id),
            ]

            # Check for variant-specific or template-level BOM
            if bom.product_id:
                domain.append(('product_id', '=', bom.product_id.id))
            else:
                domain.extend([
                    ('product_tmpl_id', '=', bom.product_tmpl_id.id),
                    ('product_id', '=', False),
                ])

            # Search for duplicates
            duplicate = self.search(domain, limit=1)
            if duplicate:
                product_name = bom.product_id.display_name if bom.product_id else bom.product_tmpl_id.display_name
                raise ValidationError(
                    _("A Master BOM with revision %s already exists for %s.\n\n"
                      "Please use a different revision number.") % (bom.revision, product_name)
                )

    # =========================================================================
    # OVERRIDES
    # =========================================================================
    def write(self, vals):
        """Track modifications in audit fields and clean code field."""
        import re

        vals['last_modified_by_id'] = self.env.user.id
        vals['last_modified_date'] = fields.Datetime.now()

        # Clean the code field if it contains "(new)" suffix
        if 'code' in vals and vals['code']:
            vals['code'] = re.sub(r'\s*\(new\)\s*\d*', '', vals['code']).strip()

        # Auto-calculate revision when converting a BOM to Master BOM
        # (checking the "Master BOM" checkbox on an existing BOM)
        if vals.get('is_master_bom') and 'revision' not in vals:
            for bom in self:
                if not bom.is_master_bom:  # Only for BOMs being converted TO master
                    # Determine next revision number
                    if bom.product_id:
                        existing_boms = self.search([
                            ('product_id', '=', bom.product_id.id),
                            ('is_master_bom', '=', True),
                        ])
                    elif bom.product_tmpl_id:
                        existing_boms = self.search([
                            ('product_tmpl_id', '=', bom.product_tmpl_id.id),
                            ('product_id', '=', False),
                            ('is_master_bom', '=', True),
                        ])
                    else:
                        existing_boms = self.env['mrp.bom']

                    # Get the highest revision and increment
                    max_revision = 0.0
                    for existing_bom in existing_boms:
                        try:
                            rev = float(existing_bom.revision)
                            if rev > max_revision:
                                max_revision = rev
                        except (ValueError, TypeError):
                            continue

                    next_revision = f"{max_revision + 1.0:.1f}"
                    vals['revision'] = next_revision
                    break  # Only update revision once for batch writes

        result = super().write(vals)

        # Force recompute display_name after code changes
        if 'code' in vals or 'revision' in vals:
            self._compute_display_name()

        # Validate revision uniqueness if revision was updated
        if 'revision' in vals:
            self._check_unique_revision()

        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure created_by and created_date are set and clean code field."""
        import re

        for vals in vals_list:
            vals.setdefault('created_by_id', self.env.user.id)
            vals.setdefault('created_date', fields.Datetime.now())

            # Auto-calculate revision for Master BOMs if not explicitly set
            if vals.get('is_master_bom') and 'revision' not in vals:
                # Determine next revision number by checking existing Master BOMs
                if vals.get('product_id'):
                    # Variant-specific BOM
                    existing_boms = self.search([
                        ('product_id', '=', vals['product_id']),
                        ('is_master_bom', '=', True),
                    ])
                elif vals.get('product_tmpl_id'):
                    # Template-level BOM
                    existing_boms = self.search([
                        ('product_tmpl_id', '=', vals['product_tmpl_id']),
                        ('product_id', '=', False),
                        ('is_master_bom', '=', True),
                    ])
                else:
                    existing_boms = self.env['mrp.bom']

                # Get the highest revision number and increment
                max_revision = 0.0
                for bom in existing_boms:
                    try:
                        rev = float(bom.revision)
                        if rev > max_revision:
                            max_revision = rev
                    except (ValueError, TypeError):
                        continue

                next_revision = f"{max_revision + 1.0:.1f}"
                vals['revision'] = next_revision
            else:
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
        - Same code as original BOM
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
        user = self.env.user.name
        date = fields.Datetime.now().strftime('%Y-%m-%d %H:%M')

        # Use the product name as BOM code (not the internal reference)
        product_code = ''
        if self.product_id:
            product_code = self.product_id.name
        elif self.product_tmpl_id:
            product_code = self.product_tmpl_id.name
        else:
            product_code = self.code or ''

        # Calculate scaling factor to normalize to 1 unit
        scaling_factor = 1.0 / self.product_qty if self.product_qty else 1.0

        # Determine next revision number by checking existing Master BOMs
        if self.product_id:
            # Variant-specific BOM
            existing_boms = self.search([
                ('product_id', '=', self.product_id.id),
                ('is_master_bom', '=', True),
            ])
        else:
            # Template-level BOM
            existing_boms = self.search([
                ('product_tmpl_id', '=', self.product_tmpl_id.id),
                ('product_id', '=', False),
                ('is_master_bom', '=', True),
            ])

        # Get the highest revision number and increment
        max_revision = 0.0
        for bom in existing_boms:
            try:
                rev = float(bom.revision)
                if rev > max_revision:
                    max_revision = rev
            except (ValueError, TypeError):
                continue

        next_revision = f"{max_revision + 1.0:.1f}"

        # Copy BOM with normalized quantity (1.0)
        # First copy without revision (copy=False field will be skipped)
        new_bom = self.copy({
            'code': product_code,  # Use product's default_code (e.g., HC-PORTMAN-DC)
            'master_bom_status': 'pending',
            'source_bom_id': self.id,
            'product_qty': 1.0,  # Normalize to 1 unit
        })

        # Then update revision explicitly (avoids copy=False issue)
        new_bom.write({
            'revision': next_revision,
            'revision_history': f"Rev {next_revision} - {date} by {user}\n  Converted from: {self.display_name} (normalized to 1 unit)\n",
        })

        # Convert lines: store product in original_product_id, clear product_id, scale quantities
        for line in new_bom.bom_line_ids:
            if line.product_id and not line.display_type:
                # Get category from line or from product
                category = line.bom_category_id or line.product_id.product_tmpl_id.bom_category_id
                # Scale the line quantity to match normalized BOM quantity
                normalized_qty = line.product_qty * scaling_factor
                line.write({
                    'original_product_id': line.product_id.id,
                    'bom_category_id': category.id if category else False,
                    'product_id': False,
                    'product_qty': normalized_qty,  # Scale quantity to match 1 unit of finished product
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
        Automatically deactivates any existing active Master BOM for the same product/variant.
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

        # Check for existing active Master BOM for the same product/variant
        # Build domain to find existing Master BOMs
        if self.product_id:
            # Variant-specific BOM: check for other variant-specific Master BOMs
            domain = [
                ('id', '!=', self.id),
                ('product_id', '=', self.product_id.id),
                ('is_master_bom', '=', True),
                ('master_bom_status', '=', 'active'),
            ]
        else:
            # Template-level BOM: check for other template-level Master BOMs
            domain = [
                ('id', '!=', self.id),
                ('product_tmpl_id', '=', self.product_tmpl_id.id),
                ('product_id', '=', False),
                ('is_master_bom', '=', True),
                ('master_bom_status', '=', 'active'),
            ]

        existing_master_boms = self.search(domain)

        # Deactivate existing Master BOMs
        if existing_master_boms:
            for old_bom in existing_master_boms:
                old_bom.write({
                    'master_bom_status': 'inactive',
                    'revision_history': (old_bom.revision_history or '') +
                                       f"  Deactivated: {fields.Datetime.now().strftime('%Y-%m-%d %H:%M')} by {self.env.user.name} (replaced by {self.display_name})\n",
                })

        user = self.env.user.name
        date = fields.Datetime.now().strftime('%Y-%m-%d %H:%M')

        self.write({
            'master_bom_status': 'active',
            'revision_history': (self.revision_history or '') + f"  Activated: {date} by {user}\n",
        })

        message = _('Master BOM %s is now active and ready for use.') % self.display_name
        sticky = False
        if existing_master_boms:
            deactivated_names = ', '.join(existing_master_boms.mapped('code_with_revision'))
            message += _('\n\n⚠️ Previous Master BOM(s) automatically deactivated:\n%s') % deactivated_names
            sticky = True  # Make sticky when deactivating old BOMs so user sees the notification

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Master BOM Activated'),
                'message': message,
                'type': 'success',
                'sticky': sticky,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_set_draft(self):
        """Set Master BOM back to draft status."""
        self.ensure_one()
        self.write({'master_bom_status': 'draft'})

    def action_submit_for_review(self):
        """Submit Draft Master BOM for review (moves to Pending status)."""
        self.ensure_one()

        if self.master_bom_status != 'draft':
            from odoo.exceptions import UserError
            raise UserError(_("Only Draft Master BOMs can be submitted for review."))

        self.write({'master_bom_status': 'pending'})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Submitted for Review'),
                'message': _('Master BOM %s is now pending review. Assign categories to all template lines before activating.') % self.display_name,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
