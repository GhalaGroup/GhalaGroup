# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockSentinelLog(models.Model):
    _name = 'stock.sentinel.log'
    _description = 'Stock Sentinel Block Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    event_type = fields.Selection(
        selection=[
            ('block', 'Blocked'),
            ('warn', 'Warned'),
            ('override', 'Overridden'),
        ],
        string='Event',
        required=True,
        readonly=True,
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
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse', readonly=True,
        ondelete='set null',
    )
    current_qty = fields.Float(
        string='On Hand', readonly=True, digits='Product Unit',
        help='On-hand quantity at the location before the operation.',
    )
    move_qty = fields.Float(
        string='Requested Qty', readonly=True, digits='Product Unit',
        help='Quantity the operation tried to remove.',
    )
    resulting_qty = fields.Float(
        string='Resulting Qty', readonly=True, digits='Product Unit',
        help='On-hand quantity that would result (negative).',
    )
    shortfall_qty = fields.Float(
        string='Shortfall', readonly=True, digits='Product Unit',
        help='How much stock was missing.',
    )
    reference = fields.Char(
        string='Document', readonly=True,
        help='Source document being processed when the event occurred.',
    )
    reason = fields.Text(
        string='Override Reason', readonly=True,
        help='Reason entered by the manager when overriding the block.',
    )
    user_id = fields.Many2one(
        'res.users', string='User', required=True, readonly=True,
        default=lambda self: self.env.user,
    )
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, readonly=True,
        default=lambda self: self.env.company,
        ondelete='cascade',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'stock.sentinel.log') or _('New')
        return super().create(vals_list)

    def _fmt_qty(self, qty):
        """Trim trailing zeros so quantities read as 3 instead of 3.0000."""
        text = ('%.4f' % (qty or 0.0)).rstrip('0').rstrip('.')
        return text or '0'

    def _notify_alert_users(self):
        """Schedule a to-do activity for the company's configured alert users."""
        todo = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not todo:
            return
        event_colors = {'block': '#DC143C', '_warn': '#B22222', 'override': '#875A7B'}
        for log in self:
            users = log.company_id.sudo().nns_alert_user_ids
            if not users:
                continue
            event_label = dict(self._fields['event_type'].selection).get(log.event_type)
            color = event_colors.get(log.event_type, '#DC143C')
            uom = log.product_id.uom_id.name or _('Units')
            # Activity notes support HTML, so format a tidy, branded block.
            note = _(
                '<div style="font-size:13px;line-height:1.6;">'
                '<span style="display:inline-block;padding:2px 8px;border-radius:10px;'
                'background-color:%(color)s;color:#fff;font-weight:600;font-size:11px;">'
                '%(event)s</span>'
                '<table style="margin-top:8px;border-collapse:collapse;">'
                '<tr><td style="padding:1px 12px 1px 0;color:#666;">Product</td>'
                '<td><strong>%(product)s</strong></td></tr>'
                '<tr><td style="padding:1px 12px 1px 0;color:#666;">Location</td>'
                '<td>%(location)s</td></tr>'
                '<tr><td style="padding:1px 12px 1px 0;color:#666;">On hand</td>'
                '<td>%(onhand)s %(uom)s</td></tr>'
                '<tr><td style="padding:1px 12px 1px 0;color:#666;">Requested</td>'
                '<td>%(requested)s %(uom)s</td></tr>'
                '<tr><td style="padding:1px 12px 1px 0;color:#666;">Shortfall</td>'
                '<td style="color:%(color)s;font-weight:600;">%(short)s %(uom)s</td></tr>'
                '</table></div>'
            ) % {
                'color': color,
                'event': event_label,
                'product': log.product_id.display_name,
                'location': log.location_id.display_name,
                'onhand': self._fmt_qty(log.current_qty),
                'requested': self._fmt_qty(log.move_qty),
                'short': self._fmt_qty(log.shortfall_qty),
                'uom': uom,
            }
            for user in users:
                log.sudo().activity_schedule(
                    act_type_xmlid='mail.mail_activity_data_todo',
                    user_id=user.id,
                    summary=_('Negative Stock %(event)s: %(product)s') % {
                        'event': event_label, 'product': log.product_id.display_name},
                    note=note,
                )
