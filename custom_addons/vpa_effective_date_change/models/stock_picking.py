# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    can_reset_to_draft = fields.Boolean(
        compute='_compute_can_reset_to_draft',
        string='Can Reset to Draft',
    )

    @api.depends('state', 'move_ids.quantity')
    def _compute_can_reset_to_draft(self):
        for rec in self:
            rec.can_reset_to_draft = (
                rec.state == 'cancel'
                and all(m.quantity == 0 for m in rec.move_ids)
            )

    def action_reset_to_draft(self):
        """Reset a cancelled transfer back to confirmed/ready state.

        Only allowed for cancellations where nothing was actually done (quantity = 0).
        Restricted to users with the 'Change Effective Date' privilege or stock managers.
        """
        self.ensure_one()

        if self.state != 'cancel':
            raise UserError(_("Only cancelled transfers can be reset to draft."))

        # Check that nothing was actually shipped/received
        done_moves = self.move_ids.filtered(lambda m: m.quantity > 0)
        if done_moves:
            raise UserError(_(
                "This transfer cannot be reset because some quantities were already processed. "
                "Please create a new transfer instead."
            ))

        # Reset moves and picking
        self.move_ids.write({'state': 'confirmed'})
        self.write({'state': 'confirmed'})

        # Try to reserve stock (assign)
        self.action_assign()

        # Log a message in chatter
        self.message_post(body=_("Transfer reset to draft by %s.") % self.env.user.name)
