# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class StockAdjustmentRequest(models.Model):
    _name = 'stock.adjustment.request'
    _description = 'Inventory Adjustment Approval Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Reference', required=True, copy=False, readonly=True,
        default=lambda self: _('New'),
    )
    state = fields.Selection(
        selection=[
            ('pending', 'Pending Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Status', default='pending', required=True, readonly=True,
        tracking=True,
    )
    product_id = fields.Many2one(
        'product.product', string='Product', required=True, readonly=True,
        ondelete='cascade',
    )
    location_id = fields.Many2one(
        'stock.location', string='Location', required=True, readonly=True,
        ondelete='cascade',
    )
    lot_id = fields.Many2one(
        'stock.lot', string='Lot/Serial', readonly=True, ondelete='cascade',
    )
    package_id = fields.Many2one(
        'stock.package', string='Package', readonly=True, ondelete='cascade',
    )
    owner_id = fields.Many2one(
        'res.partner', string='Owner', readonly=True, ondelete='cascade',
    )
    current_qty = fields.Float(
        string='Current On Hand', readonly=True, digits='Product Unit',
        help='On-hand quantity at the moment the adjustment was requested.',
    )
    counted_qty = fields.Float(
        string='Counted Qty', readonly=True, digits='Product Unit',
        help='New quantity the user counted.',
    )
    diff_qty = fields.Float(
        string='Difference', readonly=True, digits='Product Unit',
        help='Counted minus current. Positive = increase, negative = decrease.',
    )
    reason = fields.Text(
        string='Reason', required=True, readonly=True,
        help='Why this adjustment is needed.',
    )
    reject_reason = fields.Text(string='Rejection Reason', readonly=True)
    requested_by = fields.Many2one(
        'res.users', string='Requested By', required=True, readonly=True,
        default=lambda self: self.env.user,
    )
    approved_by = fields.Many2one(
        'res.users', string='Decided By', readonly=True,
    )
    decision_date = fields.Datetime(string='Decision Date', readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, readonly=True,
        default=lambda self: self.env.company, ondelete='cascade',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'stock.adjustment.request') or _('New')
        records = super().create(vals_list)
        records._notify_approvers()
        return records

    # ------------------------------------------------------------------
    # Approver resolution
    # ------------------------------------------------------------------
    def _approver_users(self):
        self.ensure_one()
        approvers = self.company_id.sudo().nns_adj_approver_ids
        if approvers:
            return approvers
        # Fall back to all Inventory Managers in the company.
        group = self.env.ref('stock.group_stock_manager', raise_if_not_found=False)
        if not group:
            return self.env['res.users']
        return group.sudo().user_ids.filtered(
            lambda u: self.company_id in u.company_ids)

    def _user_can_decide(self):
        self.ensure_one()
        if self.env.user.has_group('vpa_no_negative_stock.group_stock_sentinel_override'):
            return True
        return self.env.user in self._approver_users()

    def _notify_approvers(self):
        todo = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not todo:
            return
        for req in self:
            for user in req._approver_users():
                req.sudo().activity_schedule(
                    act_type_xmlid='mail.mail_activity_data_todo',
                    user_id=user.id,
                    summary=_('Approve Inventory Adjustment: %s') % req.product_id.display_name,
                    note=_(
                        'Inventory adjustment awaiting approval.<br/>'
                        'Product: <strong>%(product)s</strong><br/>'
                        'Location: %(location)s<br/>'
                        'Current: %(current)s &rarr; Counted: %(counted)s '
                        '(diff %(diff)s)<br/>Reason: %(reason)s'
                    ) % {
                        'product': req.product_id.display_name,
                        'location': req.location_id.display_name,
                        'current': req.current_qty,
                        'counted': req.counted_qty,
                        'diff': req.diff_qty,
                        'reason': req.reason or '',
                    },
                )

    # ------------------------------------------------------------------
    # Decision actions
    # ------------------------------------------------------------------
    def action_approve(self):
        for req in self:
            if req.state != 'pending':
                raise UserError(_('Only pending requests can be approved.'))
            if not req._user_can_decide():
                raise UserError(_(
                    'You are not allowed to approve inventory adjustments.'))
            req._apply_adjustment()
            req.write({
                'state': 'approved',
                'approved_by': self.env.user.id,
                'decision_date': fields.Datetime.now(),
            })
            req.message_post(body=_('Adjustment approved and applied.'))
            req._clear_my_activities()
        return True

    def action_open_reject_wizard(self):
        self.ensure_one()
        if self.state != 'pending':
            raise UserError(_('Only pending requests can be rejected.'))
        if not self._user_can_decide():
            raise UserError(_('You are not allowed to reject inventory adjustments.'))
        return {
            'name': _('Reject Adjustment'),
            'type': 'ir.actions.act_window',
            'res_model': 'nns.adjustment.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id},
        }

    def _do_reject(self, reject_reason):
        self.ensure_one()
        if self.state != 'pending':
            raise UserError(_('Only pending requests can be rejected.'))
        self.write({
            'state': 'rejected',
            'reject_reason': reject_reason,
            'approved_by': self.env.user.id,
            'decision_date': fields.Datetime.now(),
        })
        self.message_post(body=_('Adjustment rejected. Reason: %s') % reject_reason)
        self._clear_my_activities()

    def _clear_my_activities(self):
        """Remove the to-do activities created for approvers on this request."""
        self.activity_ids.filtered(
            lambda a: a.activity_type_id == self.env.ref(
                'mail.mail_activity_data_todo', raise_if_not_found=False)
        ).unlink()

    # ------------------------------------------------------------------
    # Apply the captured adjustment (replay) with the approval bypass flag
    # ------------------------------------------------------------------
    def _apply_adjustment(self):
        self.ensure_one()
        Quant = self.env['stock.quant'].with_context(
            inventory_mode=True, nns_adj_approved=True)
        quant = Quant._gather(
            self.product_id, self.location_id, lot_id=self.lot_id or None,
            package_id=self.package_id or None, owner_id=self.owner_id or None,
            strict=True)[:1]
        if not quant:
            quant = Quant.create({
                'product_id': self.product_id.id,
                'location_id': self.location_id.id,
                'lot_id': self.lot_id.id or False,
                'package_id': self.package_id.id or False,
                'owner_id': self.owner_id.id or False,
            })
        quant = quant.with_context(inventory_mode=True, nns_adj_approved=True)
        quant.inventory_quantity = self.counted_qty
        quant.action_apply_inventory()
