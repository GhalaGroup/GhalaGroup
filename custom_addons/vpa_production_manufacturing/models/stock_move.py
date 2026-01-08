# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

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

    def write(self, vals):
        """Override to handle product changes on template moves safely.

        When changing product on a confirmed/assigned template move:
        1. Delete existing move_lines (they reference old product)
        2. Change the product on the move
        3. Sync product_uom_qty with physical_qty_used
        4. Re-create move_lines for the new product if needed

        This prevents:
        - Orphaned move_lines referencing wrong products
        - Stock quant inconsistencies
        - Reservation mismatches
        """
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

                    # Step 1: Delete existing move_lines (they reference old product)
                    # This is safe because placeholders are consumables with no real reservations
                    if move.move_line_ids:
                        move.move_line_ids.unlink()

                    # Step 2: Set state to 'confirmed' so it can be re-assigned
                    # Note: we bypass super() here to avoid constraint issues
                    move.with_context(bypass_reservation_update=True).write({'state': 'confirmed'})

        # Step 3: Ensure product_uom_qty is set from physical_qty_used for template moves
        # This is critical - without it, "To Consume" shows 0.00
        if 'product_id' in vals and template_moves_changing_product:
            # Get the quantity to use - physical_qty_used takes priority, then master_bom_qty
            # We need to get the qty before the vals dict potentially changes it
            for move in template_moves_changing_product:
                qty = vals.get('physical_qty_used') or move.physical_qty_used or move.master_bom_qty or 1.0
                # Always set product_uom_qty to match the intended consumption
                vals = dict(vals)  # Make a copy to avoid modifying original
                vals['product_uom_qty'] = qty
                # Also ensure physical_qty_used is set if it wasn't
                if not vals.get('physical_qty_used') and not move.physical_qty_used:
                    vals['physical_qty_used'] = qty

        result = super().write(vals)

        # Step 4: Re-assign the moves to create new move_lines for the new product
        if 'product_id' in vals:
            for move in template_moves_changing_product:
                if move.state == 'confirmed':
                    # Try to assign (create move_lines) for the new product
                    try:
                        move._action_assign()
                    except Exception:
                        # If assignment fails, that's okay - product might not have stock
                        # The move will stay in 'confirmed' state (waiting for stock)
                        pass

        return result

