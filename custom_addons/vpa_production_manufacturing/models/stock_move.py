# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from markupsafe import Markup
from odoo import api, fields, models, _


class StockMove(models.Model):
    """Extend stock.move with variance tracking for MO components."""
    _inherit = 'stock.move'

    # =========================================================================
    # STOCK AVAILABILITY
    # =========================================================================
    stock_availability_state = fields.Selection([
        ('available', 'Available'),
        ('partial', 'Partial'),
        ('unavailable', 'Unavailable'),
    ], string='Stock Status', compute='_compute_stock_availability_state',
       help="Actual stock availability based on qty_available (not forecast)")

    @api.depends('product_id', 'product_qty', 'state')
    def _compute_stock_availability_state(self):
        """Compute actual stock availability (not forecast)."""
        for move in self:
            if not move.product_id or not move.product_id.is_storable:
                move.stock_availability_state = 'available'
                continue

            qty_available = move.product_id.qty_available
            if qty_available >= move.product_qty:
                move.stock_availability_state = 'available'
            elif qty_available > 0:
                move.stock_availability_state = 'partial'
            else:
                move.stock_availability_state = 'unavailable'

    # =========================================================================
    # TEMPLATE LINE SUPPORT
    # =========================================================================
    bom_category_id = fields.Many2one(
        'vpa.bom.category',
        string='BOM Category',
        help="Category from template BOM line for product filtering",
    )
    template_line_description = fields.Char(
        string='Template Description',
        help="Description from template BOM line for worker reference",
    )
    is_template_move = fields.Boolean(
        string='Is Template Move',
        compute='_compute_is_template_move',
        store=True,
        help="True if this move was created from a template BOM line",
    )
    is_placeholder_product = fields.Boolean(
        string='Is Placeholder Product',
        compute='_compute_is_placeholder_product',
        store=True,
        help="True if this move still has a placeholder product that needs to be replaced",
    )

    # =========================================================================
    # VARIANCE TRACKING FIELDS
    # =========================================================================
    master_bom_qty = fields.Float(
        string='Master BOM Qty',
        digits='Product Unit of Measure',
        readonly=True,
        help="Original quantity from Master BOM template line",
    )
    physical_qty_used = fields.Float(
        string='Physical Qty Used',
        digits='Product Unit of Measure',
        help="Actual quantity physically consumed (entered by worker)",
    )
    qty_variance = fields.Float(
        string='Qty Variance',
        compute='_compute_qty_variance',
        store=True,
        digits='Product Unit of Measure',
        help="Difference: Physical Qty Used - Master BOM Qty (positive = over-consumed)",
    )
    variance_percentage = fields.Float(
        string='Variance %',
        compute='_compute_qty_variance',
        store=True,
        digits=(5, 2),
        help="Variance as percentage of Master BOM Qty",
    )
    variance_display = fields.Char(
        string='Variance',
        compute='_compute_variance_display',
        help="Variance displayed as qty (percentage)",
    )

    @api.depends('bom_category_id')
    def _compute_is_template_move(self):
        """A template move has a category (originated from template BOM line)."""
        for move in self:
            move.is_template_move = bool(move.bom_category_id)

    @api.depends('product_id')
    def _compute_product_uom(self):
        """Override to preserve UoM for template moves.

        Standard Odoo sets product_uom = product_id.uom_id when product changes.
        For template moves, we need to keep the BOM line's UoM (e.g., m³) even when
        the user selects a different product, because the variance tracking uses
        the BOM's UoM.
        """
        for move in self:
            # For template moves with existing UoM, preserve it
            if move.bom_category_id and move.product_uom:
                # Keep existing UoM - don't let product change override it
                continue
            # For non-template moves, use standard behavior
            if move.product_id:
                move.product_uom = move.product_id.uom_id.id

    @api.depends('product_id', 'product_id.product_tmpl_id.is_template_placeholder')
    def _compute_is_placeholder_product(self):
        """Check if this move has a placeholder product that needs to be replaced."""
        for move in self:
            if move.product_id and hasattr(move.product_id.product_tmpl_id, 'is_template_placeholder'):
                move.is_placeholder_product = move.product_id.product_tmpl_id.is_template_placeholder
            else:
                move.is_placeholder_product = False

    @api.depends('master_bom_qty', 'physical_qty_used')
    def _compute_qty_variance(self):
        """Calculate variance between planned and actual quantities."""
        for move in self:
            if move.master_bom_qty:
                move.qty_variance = move.physical_qty_used - move.master_bom_qty
                move.variance_percentage = (move.qty_variance / move.master_bom_qty) * 100
            else:
                move.qty_variance = 0.0
                move.variance_percentage = 0.0

    @api.depends('qty_variance', 'variance_percentage', 'is_template_move')
    def _compute_variance_display(self):
        """Format variance as 'qty (percentage%)' for display."""
        for move in self:
            if not move.is_template_move or move.qty_variance == 0:
                move.variance_display = "0.00 (0%)"
            else:
                # Format: +1.50 (+15.0%) or -0.50 (-5.0%)
                sign = '+' if move.qty_variance > 0 else ''
                move.variance_display = f"{sign}{move.qty_variance:.2f} ({sign}{move.variance_percentage:.1f}%)"

    @api.onchange('physical_qty_used')
    def _onchange_physical_qty_used(self):
        """Sync physical_qty_used with product_uom_qty for consumption."""
        if self.is_template_move and self.physical_qty_used:
            self.product_uom_qty = self.physical_qty_used

    @api.onchange('product_id')
    def _onchange_product_id_template(self):
        """When product is selected for template move, default physical qty and refresh availability."""
        if self.is_template_move and self.product_id and not self.physical_qty_used:
            # Default physical qty to master bom qty when product is first selected
            self.physical_qty_used = self.master_bom_qty

        # Force recompute stock availability for the new product
        # This ensures the availability badge updates in the UI
        if self.product_id:
            self._compute_stock_availability_state()

    def _is_placeholder_product(self):
        """Check if this move has a placeholder product."""
        self.ensure_one()
        if self.product_id and hasattr(self.product_id.product_tmpl_id, 'is_template_placeholder'):
            return self.product_id.product_tmpl_id.is_template_placeholder
        return False

    # =========================================================================
    # COMPONENT AUDIT TRAIL - Track changes to MO chatter
    # =========================================================================
    def _get_mo_tracked_fields(self):
        """Return dict of fields to track for MO component changes."""
        return {
            'product_id': 'Product',
            'product_uom_qty': 'Quantity',
            'product_uom': 'UoM',
            'physical_qty_used': 'Physical Qty Used',
        }

    def _format_mo_field_value(self, field_name, value):
        """Format field value for display in MO tracking message."""
        if value is False or value is None:
            return _("(empty)")
        if field_name in ('product_id', 'product_uom'):
            return value.display_name if value else _("(empty)")
        if field_name in ('product_uom_qty', 'physical_qty_used'):
            return f"{value:.2f}" if value else "0.00"
        return str(value) if value else _("(empty)")

    def _should_track_component(self):
        """Check if this move should be tracked as an MO component change."""
        return (
            self.raw_material_production_id
            and not self.env.context.get('skip_component_tracking')
        )

    @api.model_create_multi
    def create(self, vals_list):
        """Track component additions to MO chatter."""
        moves = super().create(vals_list)

        if self.env.context.get('skip_component_tracking'):
            return moves

        # Group added components by MO
        moves_by_mo = {}
        for move in moves:
            if move.raw_material_production_id and move.product_id:
                mo_id = move.raw_material_production_id.id
                if mo_id not in moves_by_mo:
                    moves_by_mo[mo_id] = {
                        'mo': move.raw_material_production_id,
                        'components': [],
                    }
                uom_name = move.product_uom.name if move.product_uom else ''
                qty = move.product_uom_qty or 0
                moves_by_mo[mo_id]['components'].append(
                    f"{move.product_id.display_name} ({qty:.2f} {uom_name})"
                )

        # Post messages
        for mo_id, data in moves_by_mo.items():
            mo = data['mo']
            if mo.exists() and data['components']:
                msg = "<strong>Component Added:</strong><ul>"
                for comp in data['components']:
                    msg += f"<li>{comp}</li>"
                msg += "</ul>"
                mo.message_post(body=Markup(msg), message_type='notification')

        return moves

    def unlink(self):
        """Track component removals from MO chatter."""
        if self.env.context.get('skip_component_tracking'):
            return super().unlink()

        # Capture component info BEFORE deletion
        moves_by_mo = {}
        for move in self:
            if move.raw_material_production_id and move.product_id:
                mo_id = move.raw_material_production_id.id
                if mo_id not in moves_by_mo:
                    moves_by_mo[mo_id] = {
                        'mo': move.raw_material_production_id,
                        'components': [],
                    }
                uom_name = move.product_uom.name if move.product_uom else ''
                qty = move.product_uom_qty or 0
                moves_by_mo[mo_id]['components'].append(
                    f"{move.product_id.display_name} ({qty:.2f} {uom_name})"
                )

        result = super().unlink()

        # Post messages after successful deletion
        for mo_id, data in moves_by_mo.items():
            mo = data['mo']
            if mo.exists() and data['components']:
                msg = "<strong>Component Removed:</strong><ul>"
                for comp in data['components']:
                    msg += f"<li>{comp}</li>"
                msg += "</ul>"
                mo.message_post(body=Markup(msg), message_type='notification')

        return result

    def write(self, vals):
        """Override to handle template moves and track component changes.

        When changing product on a confirmed/assigned template move:
        1. Delete existing move_lines (they reference old product)
        2. Change the product on the move
        3. Sync product_uom_qty with physical_qty_used
        4. Re-create move_lines for the new product if needed

        Also tracks all component field changes to the MO chatter.
        """
        # -----------------------------------------------------------------
        # 1. CAPTURE old values for tracking BEFORE any changes
        # -----------------------------------------------------------------
        tracked_fields = self._get_mo_tracked_fields()
        changes_by_mo = {}  # {mo_id: {'mo': record, 'changes': [...]}}
        skip_tracking = self.env.context.get('skip_component_tracking')

        if not skip_tracking:
            for move in self:
                if not move.raw_material_production_id:
                    continue
                mo_id = move.raw_material_production_id.id

                for field_name, label in tracked_fields.items():
                    if field_name in vals:
                        old_value = getattr(move, field_name)
                        new_value = vals[field_name]

                        # For Many2one fields, resolve the new record
                        if field_name in ('product_id', 'product_uom') and new_value:
                            field_obj = self._fields[field_name]
                            new_record = self.env[field_obj.comodel_name].browse(new_value)
                        else:
                            new_record = new_value

                        old_formatted = move._format_mo_field_value(field_name, old_value)
                        new_formatted = move._format_mo_field_value(field_name, new_record)

                        if old_formatted != new_formatted:
                            if mo_id not in changes_by_mo:
                                changes_by_mo[mo_id] = {
                                    'mo': move.raw_material_production_id,
                                    'changes': [],
                                }
                            line_ref = move.product_id.display_name if move.product_id else f"Move #{move.id}"
                            changes_by_mo[mo_id]['changes'].append({
                                'line_ref': line_ref,
                                'field_label': label,
                                'old_value': old_formatted,
                                'new_value': new_formatted,
                            })

        # -----------------------------------------------------------------
        # 2. TEMPLATE MOVE PRODUCT CHANGE HANDLING (existing logic)
        # -----------------------------------------------------------------
        template_moves_changing_product = self.env['stock.move']

        if 'product_id' in vals:
            for move in self:
                # Only handle template moves that are already assigned/confirmed
                if move.is_template_move and move.state in ('assigned', 'confirmed', 'partially_available'):
                    old_product = move.product_id
                    new_product_id = vals.get('product_id')

                    # Skip if product isn't actually changing
                    if old_product.id == new_product_id:
                        continue

                    template_moves_changing_product |= move

                    # Delete existing move_lines (they reference old product)
                    if move.move_line_ids:
                        move.move_line_ids.unlink()

                    # Set state to 'confirmed' so it can be re-assigned
                    move.with_context(
                        bypass_reservation_update=True,
                        skip_component_tracking=True,
                    ).write({'state': 'confirmed'})

        # Ensure product_uom_qty is set from physical_qty_used for template moves
        if 'product_id' in vals and template_moves_changing_product:
            for move in template_moves_changing_product:
                qty = vals.get('physical_qty_used') or move.physical_qty_used or move.master_bom_qty or 1.0
                vals = dict(vals)
                vals['product_uom_qty'] = qty
                if not vals.get('physical_qty_used') and not move.physical_qty_used:
                    vals['physical_qty_used'] = qty

        # -----------------------------------------------------------------
        # 3. PERFORM THE WRITE
        # -----------------------------------------------------------------
        result = super().write(vals)

        # -----------------------------------------------------------------
        # 4. RE-ASSIGN template moves for new product
        # -----------------------------------------------------------------
        if 'product_id' in vals:
            for move in template_moves_changing_product:
                if move.state == 'confirmed':
                    try:
                        move._action_assign()
                    except Exception:
                        pass

        # -----------------------------------------------------------------
        # 5. POST TRACKING MESSAGES to MO chatter
        # -----------------------------------------------------------------
        if not skip_tracking:
            for mo_id, data in changes_by_mo.items():
                if data['changes']:
                    mo = data['mo']
                    if mo.exists():
                        msg_lines = ["<strong>Component Changes:</strong><ul>"]
                        for change in data['changes']:
                            msg_lines.append(
                                f"<li><b>{change['line_ref']}</b>: {change['field_label']} "
                                f"changed from <i>{change['old_value']}</i> "
                                f"to <i>{change['new_value']}</i></li>"
                            )
                        msg_lines.append("</ul>")
                        mo.message_post(
                            body=Markup(''.join(msg_lines)),
                            message_type='notification',
                        )

        return result
