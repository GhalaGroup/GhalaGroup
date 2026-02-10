# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Software Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class MoSplitWizardLine(models.TransientModel):
    _name = 'vpa.mo.split.wizard.line'
    _description = 'Split Manufacturing Order Line'
    _order = 'sequence, id'

    wizard_id = fields.Many2one(
        'vpa.mo.split.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    lot_number = fields.Integer(
        string='Lot #',
        compute='_compute_lot_number',
        store=False,
        readonly=True,
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=0.0,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )

    @api.depends('wizard_id.line_ids', 'sequence')
    def _compute_lot_number(self):
        """Compute lot number based on position in sorted list."""
        for line in self:
            if line.wizard_id:
                # Get all lines for this wizard, sorted by sequence then id
                # Use lambda to sort by sequence first, then by id (if available)
                sorted_lines = line.wizard_id.line_ids.sorted(lambda l: (l.sequence, l.id or 0))
                # Find this line's position by object reference (not ID)
                for idx, sorted_line in enumerate(sorted_lines, start=1):
                    if sorted_line == line:
                        line.lot_number = idx
                        break
                else:
                    line.lot_number = 1
            else:
                line.lot_number = 1

    # lot_number is now computed, no need for create() or unlink() overrides


class MoSplitWizard(models.TransientModel):
    _name = 'vpa.mo.split.wizard'
    _description = 'Split Manufacturing Order Wizard'

    production_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing Order',
        required=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        related='production_id.product_id',
        readonly=True,
    )
    original_qty = fields.Float(
        string='Original Quantity',
        related='production_id.product_qty',
        readonly=True,
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        related='production_id.product_uom_id',
        readonly=True,
    )
    line_ids = fields.One2many(
        'vpa.mo.split.wizard.line',
        'wizard_id',
        string='Lot Lines',
    )
    total_qty = fields.Float(
        string='Total Quantity',
        compute='_compute_total_qty',
        store=True,
    )

    @api.depends('line_ids.quantity')
    def _compute_total_qty(self):
        """Calculate total quantity from all lot lines."""
        for wizard in self:
            wizard.total_qty = sum(line.quantity for line in wizard.line_ids)

    @api.model
    def default_get(self, fields_list):
        """Initialize wizard with 2 default lot lines."""
        res = super().default_get(fields_list)

        # Get production_id from context
        production_id = self.env.context.get('default_production_id')
        if production_id:
            production = self.env['mrp.production'].browse(production_id)

            # Create 2 default lot lines (don't pass lot_number - it's computed)
            res['line_ids'] = [
                (0, 0, {'quantity': production.product_qty, 'sequence': 10}),
                (0, 0, {'quantity': 0.0, 'sequence': 20}),
            ]

        return res

    # No need for write() override - lot numbers are computed automatically

    def action_add_lot(self):
        """Add another lot line to the wizard."""
        self.ensure_one()

        # Get next lot number and sequence
        existing_lot_numbers = self.line_ids.mapped('lot_number')
        next_lot_number = max(existing_lot_numbers) + 1 if existing_lot_numbers else 1

        existing_sequences = self.line_ids.mapped('sequence')
        next_sequence = max(existing_sequences) + 10 if existing_sequences else 10

        # Add new line - the create() method will auto-assign lot_number
        self.write({
            'line_ids': [(0, 0, {
                'quantity': 0.0,
                'sequence': next_sequence,
            })]
        })

        # Reopen wizard
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.mo.split.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_split(self):
        """Execute the MO split."""
        self.ensure_one()

        # Log wizard state for debugging
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f'=== SPLIT MO WIZARD DEBUG ===')
        _logger.info(f'Production ID: {self.production_id.id} ({self.production_id.name})')
        _logger.info(f'Original Qty: {self.original_qty}')
        _logger.info(f'Total Qty: {self.total_qty}')
        _logger.info(f'Line IDs count: {len(self.line_ids)}')
        for line in self.line_ids:
            _logger.info(f'  Line: Lot #{line.lot_number}, Qty: {line.quantity}')

        # Validate this MO hasn't already been split
        if self.production_id.lot_reference:
            raise UserError(_(
                'This Manufacturing Order has already been split (Lot Reference: %s). '
                'You cannot split it again.'
            ) % self.production_id.lot_reference)

        # Validate total quantity
        if self.total_qty != self.original_qty:
            raise UserError(_(
                'Total quantity (%.2f) must equal original MO quantity (%.2f).'
            ) % (self.total_qty, self.original_qty))

        # Validate at least 2 lots
        if len(self.line_ids) < 2:
            raise UserError(_('You must have at least 2 lots to split an MO.'))

        # Validate no zero quantities
        if any(line.quantity <= 0 for line in self.line_ids):
            raise UserError(_('All lot quantities must be greater than zero.'))

        # Validate no individual lot exceeds original quantity
        max_lot_qty = max(line.quantity for line in self.line_ids)
        if max_lot_qty > self.original_qty:
            raise UserError(_(
                'Individual lot quantity (%.2f) cannot exceed the original MO quantity (%.2f). '
                'If you need to produce more, please update the MO quantity first.'
            ) % (max_lot_qty, self.original_qty))

        # Sort lines by sequence
        lines = self.line_ids.sorted('sequence')
        total_lots = len(lines)

        # Update original MO to first lot quantity
        first_lot = lines[0]
        self.production_id.write({
            'product_qty': first_lot.quantity,
            'lot_reference': f'LOT 1/{total_lots}',
        })

        # Create new MOs for remaining lots
        created_mos = [self.production_id.name]
        _logger.info(f'Creating {len(lines)-1} new MOs...')

        for idx, line in enumerate(lines[1:], start=2):
            _logger.info(f'Creating MO for LOT {idx}/{total_lots}, Qty: {line.quantity}')

            # Copy the original MO with explicit context
            new_mo = self.production_id.with_context(
                vpa_explicit_product_qty=line.quantity
            ).copy({
                'product_qty': line.quantity,
                'lot_reference': f'LOT {idx}/{total_lots}',
            })
            _logger.info(f'Created new MO: {new_mo.name} (ID: {new_mo.id}), Qty: {new_mo.product_qty}')
            created_mos.append(new_mo.name)

            # Force write to preserve origin and quantity (copy() doesn't always preserve these)
            update_vals = {}
            if new_mo.origin != self.production_id.origin:
                _logger.info(f'Preserving origin: {self.production_id.origin}')
                update_vals['origin'] = self.production_id.origin
            if new_mo.product_qty != line.quantity:
                _logger.info(f'Forcing quantity update from {new_mo.product_qty} to {line.quantity}')
                update_vals['product_qty'] = line.quantity

            if update_vals:
                new_mo.write(update_vals)

        # Post detailed history messages
        current_user = self.env.user
        note_subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')

        # Message for the original MO (now Lot 1)
        original_msg = _(
            'MO split by %s into %d lots: %s. This MO is now LOT 1/%d with quantity %.2f %s.'
        ) % (
            current_user.name,
            total_lots,
            ', '.join(created_mos),
            total_lots,
            lines[0].quantity,
            self.product_uom_id.name
        )
        self.production_id.message_post(
            body=original_msg,
            message_type='notification',
            subtype_id=note_subtype_id
        )

        # Post message on each newly created MO
        for idx, line in enumerate(lines[1:], start=2):
            new_mo = self.env['mrp.production'].search([
                ('lot_reference', '=', f'LOT {idx}/{total_lots}'),
                ('origin', '=', self.production_id.origin),
                ('product_id', '=', self.production_id.product_id.id),
            ], limit=1)

            if new_mo:
                new_mo_msg = _(
                    'Created by %s via MO split from %s. This is LOT %d/%d with quantity %.2f %s.'
                ) % (
                    current_user.name,
                    self.production_id.name,
                    idx,
                    total_lots,
                    line.quantity,
                    self.product_uom_id.name
                )
                new_mo.message_post(
                    body=new_mo_msg,
                    message_type='notification',
                    subtype_id=note_subtype_id
                )

        # Post message on the related Sales Order if it exists
        if self.production_id.origin:
            sale_order = self.env['sale.order'].search([
                ('name', '=', self.production_id.origin)
            ], limit=1)

            if sale_order:
                # Build detailed lot breakdown
                lot_details = []
                for idx, line in enumerate(lines, start=1):
                    mo_name = created_mos[idx-1] if idx == 1 else created_mos[idx-1]
                    lot_details.append(f'• LOT {idx}/{total_lots}: {mo_name} ({line.quantity} {self.product_uom_id.name})')

                so_msg = _(
                    'MO %s split by %s into %d lots for product %s:\n%s'
                ) % (
                    self.production_id.name,
                    current_user.name,
                    total_lots,
                    self.production_id.product_id.display_name,
                    '\n'.join(lot_details)
                )
                sale_order.message_post(
                    body=so_msg,
                    message_type='notification',
                    subtype_id=note_subtype_id
                )

        # Show success notification
        success_message = _('MO split into %d lots: %s') % (total_lots, ', '.join(created_mos))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('MO Split Successfully'),
                'message': success_message,
                'type': 'success',
                'sticky': False,
            }
        }
