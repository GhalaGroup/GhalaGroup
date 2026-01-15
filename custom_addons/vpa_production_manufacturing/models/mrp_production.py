# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    """Extend mrp.production to handle template BOM lines with variance tracking."""
    _inherit = 'mrp.production'

    has_template_moves = fields.Boolean(
        string='Has Template Components',
        compute='_compute_has_template_moves',
        store=True,
        help="True if MO has component moves from template BOM lines",
    )
    template_moves_pending = fields.Boolean(
        string='Template Moves Pending',
        compute='_compute_template_moves_pending',
        help="True if some template moves still have placeholder products",
    )

    @api.depends('move_raw_ids.is_template_move')
    def _compute_has_template_moves(self):
        """Check if MO has any template moves."""
        for production in self:
            production.has_template_moves = any(
                move.is_template_move for move in production.move_raw_ids
            )

    @api.depends('move_raw_ids', 'move_raw_ids.is_template_move', 'move_raw_ids.product_id')
    def _compute_template_moves_pending(self):
        """Check if any template moves still have placeholder products."""
        for production in self:
            template_moves = production.move_raw_ids.filtered(lambda m: m.is_template_move)
            if not template_moves:
                production.template_moves_pending = False
            else:
                # Check if any template move has a placeholder product
                production.template_moves_pending = any(
                    move._is_placeholder_product() for move in template_moves
                )

    @api.depends('company_id', 'bom_id', 'product_id', 'product_qty', 'product_uom_id', 'location_src_id', 'never_product_template_attribute_value_ids')
    def _compute_move_raw_ids(self):
        """Override to preserve template move custom fields during recomputation.

        Standard Odoo overwrites ALL move fields when recomputing, which would wipe out:
        - User's product selection (changed from placeholder to real product)
        - User's physical_qty_used values
        - bom_category_id, template_line_description, master_bom_qty

        This override preserves these values for template moves.
        """
        from odoo import Command

        for production in self:
            if production.state != 'draft' or self.env.context.get('skip_compute_move_raw_ids'):
                continue

            # Preserve custom fields from existing template moves BEFORE standard compute
            template_move_data = {}
            for move in production.move_raw_ids.filtered(lambda m: m.bom_line_id and m.bom_category_id):
                template_move_data[move.bom_line_id.id] = {
                    'product_id': move.product_id.id,
                    'bom_category_id': move.bom_category_id.id,
                    'template_line_description': move.template_line_description,
                    'master_bom_qty': move.master_bom_qty,
                    'physical_qty_used': move.physical_qty_used,
                    'product_uom': move.product_uom.id,  # Preserve UoM
                }

            # Build the move list similar to standard Odoo
            list_move_raw = [Command.link(move.id) for move in production.move_raw_ids.filtered(lambda m: not m.bom_line_id)]

            if not production.bom_id and not production._origin.product_id:
                production.move_raw_ids = list_move_raw
                continue

            if any(move.bom_line_id.bom_id != production.bom_id or move.bom_line_id._skip_bom_line(production.product_id, production.never_product_template_attribute_value_ids)
                for move in production.move_raw_ids if move.bom_line_id):
                production.move_raw_ids = [Command.clear()]
                template_move_data = {}  # Clear preserved data if BOM changed

            if production.bom_id and production.product_id and production.product_qty > 0:
                moves_raw_values = production._get_moves_raw_values()
                move_raw_dict = {move.bom_line_id.id: move for move in production.move_raw_ids.filtered(lambda m: m.bom_line_id)}

                for move_raw_values in moves_raw_values:
                    bom_line_id = move_raw_values['bom_line_id']

                    # Restore preserved template move data
                    if bom_line_id in template_move_data:
                        preserved = template_move_data[bom_line_id]
                        # Only restore product_id if user changed it from placeholder
                        if preserved['product_id']:
                            move_raw_values['product_id'] = preserved['product_id']
                        move_raw_values['bom_category_id'] = preserved['bom_category_id']
                        move_raw_values['template_line_description'] = preserved['template_line_description']
                        move_raw_values['master_bom_qty'] = preserved['master_bom_qty']
                        move_raw_values['physical_qty_used'] = preserved['physical_qty_used']
                        move_raw_values['product_uom'] = preserved['product_uom']

                    if bom_line_id in move_raw_dict:
                        list_move_raw += [Command.update(move_raw_dict[bom_line_id].id, move_raw_values)]
                    else:
                        list_move_raw += [Command.create(move_raw_values)]

                production.move_raw_ids = list_move_raw
            else:
                production.move_raw_ids = [Command.delete(move.id) for move in production.move_raw_ids.filtered(lambda m: m.bom_line_id)]

    def _get_moves_raw_values(self):
        """Override to handle template BOM lines with placeholder products."""
        moves = []
        for production in self:
            if not production.bom_id:
                continue
            factor = production.product_uom_id._compute_quantity(
                production.product_qty,
                production.bom_id.product_uom_id,
                round=False
            ) / production.bom_id.product_qty

            _boms, lines = production.bom_id.explode(
                production.product_id,
                factor,
                picking_type=production.bom_id.picking_type_id,
                never_attribute_values=production.never_product_template_attribute_value_ids
            )

            for bom_line, line_data in lines:
                # Check if this is a template line (has category but no product)
                is_template = hasattr(bom_line, 'is_template_line') and bom_line.is_template_line

                if is_template:
                    # Template line - use placeholder product from category
                    if bom_line.bom_category_id and bom_line.bom_category_id.placeholder_product_id:
                        placeholder = bom_line.bom_category_id.placeholder_product_id
                        operation = bom_line.operation_id.id or (
                            line_data['parent_line'] and line_data['parent_line'].operation_id.id
                        )
                        moves.append(production._get_move_raw_values(
                            placeholder,
                            line_data['qty'],
                            bom_line.product_uom_id,
                            operation,
                            bom_line
                        ))
                else:
                    # Standard line - use normal logic
                    if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom':
                        continue
                    if bom_line.product_id.type != 'consu':
                        continue
                    operation = bom_line.operation_id.id or (
                        line_data['parent_line'] and line_data['parent_line'].operation_id.id
                    )
                    moves.append(production._get_move_raw_values(
                        bom_line.product_id,
                        line_data['qty'],
                        bom_line.product_uom_id,
                        operation,
                        bom_line
                    ))

        return moves

    def _get_move_raw_values(self, product, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        """Override to add template line fields to move values."""
        values = super()._get_move_raw_values(product, product_uom_qty, product_uom, operation_id, bom_line)

        # Add template line fields if this is from a template BOM line
        if bom_line and hasattr(bom_line, 'is_template_line') and bom_line.is_template_line:
            values.update({
                'bom_category_id': bom_line.bom_category_id.id if bom_line.bom_category_id else False,
                'template_line_description': bom_line.line_description or '',
                'master_bom_qty': product_uom_qty,
                'physical_qty_used': product_uom_qty,  # Default to same as planned
            })

        return values

    def write(self, vals):
        """Override to preserve template move custom fields during UI saves.

        When the UI saves an MO, it sends move_raw_ids data without our custom fields.
        This would wipe out bom_category_id, master_bom_qty, etc.
        We preserve these before the write and restore them after.

        Additionally, if moves are missing template data but their BOM line is a template
        line, we populate the data from the BOM line.
        """
        # Preserve template move data before write
        preserved_data = {}
        if 'move_raw_ids' in vals:
            for production in self:
                preserved_data[production.id] = {}
                for move in production.move_raw_ids.filtered(lambda m: m.bom_line_id):
                    preserved_data[production.id][move.bom_line_id.id] = {
                        'move_id': move.id,
                        'bom_category_id': move.bom_category_id.id if move.bom_category_id else False,
                        'template_line_description': move.template_line_description,
                        'master_bom_qty': move.master_bom_qty,
                        'physical_qty_used': move.physical_qty_used,
                        'product_uom': move.product_uom.id,
                    }

        result = super().write(vals)

        # Restore or populate template move data after write
        if 'move_raw_ids' in vals:
            for production in self:
                for move in production.move_raw_ids.filtered(lambda m: m.bom_line_id):
                    bom_line = move.bom_line_id
                    bom_line_id = bom_line.id

                    # Skip if move already has template data
                    if move.bom_category_id:
                        continue

                    # Try to restore from preserved data first
                    if production.id in preserved_data and bom_line_id in preserved_data[production.id]:
                        preserved = preserved_data[production.id][bom_line_id]
                        if preserved['bom_category_id']:
                            move.write({
                                'bom_category_id': preserved['bom_category_id'],
                                'template_line_description': preserved['template_line_description'],
                                'master_bom_qty': preserved['master_bom_qty'],
                                'physical_qty_used': preserved['physical_qty_used'],
                                'product_uom': preserved['product_uom'],
                            })
                            continue

                    # If BOM line is a template line, populate data from it
                    if hasattr(bom_line, 'is_template_line') and bom_line.is_template_line and bom_line.bom_category_id:
                        move.write({
                            'bom_category_id': bom_line.bom_category_id.id,
                            'template_line_description': bom_line.line_description or '',
                            'master_bom_qty': move.product_uom_qty,
                            'physical_qty_used': move.product_uom_qty,
                        })

        return result

    def _get_consumption_issues(self):
        """Override to handle template moves in consumption validation.

        Standard Odoo compares BOM expected quantities against actual move quantities
        by product. For template moves, the BOM product (placeholder) differs from the
        actual product (real product), causing false positives.

        This override:
        1. Uses the actual move's product_uom_qty as expected (for template moves)
        2. Compares against physical_qty_used instead of BOM placeholder quantities
        """
        from collections import defaultdict

        issues = []
        if self.env.context.get('skip_consumption', False):
            return issues

        for order in self:
            if order.consumption == 'flexible' or not order.bom_id or not order.bom_id.bom_line_ids:
                continue

            # For MOs with template moves, use actual move data instead of BOM
            if order.has_template_moves:
                # Build expected quantities from actual moves (not BOM)
                # Template moves use their product_uom_qty as the "expected" amount
                expected_qty_by_product = defaultdict(float)
                for move in order.move_raw_ids:
                    if move.state == 'cancel':
                        continue
                    # For template moves, expected = product_uom_qty (which includes physical_qty_used)
                    # For non-template moves, also use product_uom_qty
                    move_product_qty = move.product_uom._compute_quantity(
                        move.product_uom_qty, move.product_id.uom_id
                    )
                    expected_qty_by_product[move.product_id] += move_product_qty * order.qty_producing / order.product_qty

                # Build done quantities from actual moves
                done_qty_by_product = defaultdict(float)
                for move in order.move_raw_ids:
                    if move.state == 'cancel':
                        continue
                    quantity = move.product_uom._compute_quantity(
                        move._get_picked_quantity(), move.product_id.uom_id
                    )
                    done_qty_by_product[move.product_id] += quantity if move.picked else 0.0

                # Compare expected vs done for each product
                for product, qty_to_consume in expected_qty_by_product.items():
                    quantity = done_qty_by_product.get(product, 0.0)
                    if product.uom_id.compare(qty_to_consume, quantity) != 0:
                        issues.append((order, product, quantity, qty_to_consume))

                # Check for extra products not in expected
                for product, quantity in done_qty_by_product.items():
                    if product not in expected_qty_by_product and not product.uom_id.is_zero(quantity):
                        issues.append((order, product, quantity, 0.0))
            else:
                # Standard behavior for non-template MOs
                expected_move_values = order._get_moves_raw_values()
                expected_qty_by_product = defaultdict(float)
                for move_values in expected_move_values:
                    move_product = self.env['product.product'].browse(move_values['product_id'])
                    move_uom = self.env['uom.uom'].browse(move_values['product_uom'])
                    move_product_qty = move_uom._compute_quantity(move_values['product_uom_qty'], move_product.uom_id)
                    expected_qty_by_product[move_product] += move_product_qty * order.qty_producing / order.product_qty

                done_qty_by_product = defaultdict(float)
                for move in order.move_raw_ids:
                    quantity = move.product_uom._compute_quantity(move._get_picked_quantity(), move.product_id.uom_id)
                    # extra lines with non-zero qty picked
                    if move.product_id not in expected_qty_by_product and move.picked and not move.product_id.uom_id.is_zero(quantity):
                        issues.append((order, move.product_id, quantity, 0.0))
                        continue
                    done_qty_by_product[move.product_id] += quantity if move.picked else 0.0

                # origin lines from bom with different qty
                for product, qty_to_consume in expected_qty_by_product.items():
                    quantity = done_qty_by_product.get(product, 0.0)
                    if product.uom_id.compare(qty_to_consume, quantity) != 0:
                        issues.append((order, product, quantity, qty_to_consume))

        return issues

    def button_mark_done(self):
        """Override to validate all template moves have real products before completion."""
        for production in self:
            if production.has_template_moves:
                # Check for moves with placeholder products
                placeholder_moves = production.move_raw_ids.filtered(
                    lambda m: m.is_template_move and m._is_placeholder_product()
                )
                if placeholder_moves:
                    # Build error message with list of incomplete moves
                    move_names = []
                    for move in placeholder_moves:
                        category = move.bom_category_id.name if move.bom_category_id else 'Unknown'
                        desc = move.template_line_description or ''
                        if desc:
                            move_names.append(f"- {category} ({desc})")
                        else:
                            move_names.append(f"- {category}")

                    raise UserError(_(
                        "Cannot complete Manufacturing Order.\n\n"
                        "The following template components still have placeholder products. "
                        "Please select the actual products used:\n\n%s"
                    ) % '\n'.join(move_names))

        return super().button_mark_done()

    @api.onchange('product_id')
    def _onchange_product_id_auto_select_master_bom(self):
        """Automatically select the Master BOM when product is chosen.

        If product has multiple BOMs, prefer the active Master BOM.
        """
        if self.product_id:
            # Find active Master BOM for this product
            master_bom = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                ('is_master_bom', '=', True),
                ('master_bom_status', '=', 'active'),
                ('active', '=', True),
            ], limit=1)

            if master_bom:
                self.bom_id = master_bom
