# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class VpaCommissionLine(models.Model):
    _name = 'vpa.commission.line'
    _description = 'Commission Line'
    _order = 'date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    scheme_id = fields.Many2one(
        'vpa.commission.scheme',
        string='Commission Scheme',
        required=True,
        ondelete='cascade',
        index=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        related='scheme_id.employee_id',
        store=True,
        index=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='scheme_id.company_id',
        store=True,
    )

    # Type field
    type = fields.Selection([
        ('production', 'Production'),
        ('sales', 'Sales'),
        ('manual', 'Manual'),
    ], string='Type', default='production', required=True)

    date = fields.Date(
        string='Date',
        required=True,
        index=True,
        help='Manufacturing Order completion date',
    )
    @api.model
    def _get_year_selection(self):
        """Generate year selection from 2020 to current year + 2."""
        current_year = fields.Date.today().year
        return [(str(y), str(y)) for y in range(2020, current_year + 3)]

    date_year = fields.Selection(
        selection='_get_year_selection',
        string='Year',
        compute='_compute_date_parts',
        store=True,
        index=True,
    )
    date_month = fields.Char(
        string='Month',
        compute='_compute_date_parts',
        store=True,
        index=True,
    )

    # Source documents
    production_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing Order',
        index=True,
        ondelete='set null',
    )
    sale_order_name = fields.Char(
        string='Sales Order',
        compute='_compute_sale_order_info',
        store=True,
        readonly=False,
    )
    item_name = fields.Char(
        string='Item',
        compute='_compute_sale_order_info',
        store=True,
        readonly=False,
    )
    customer_ref = fields.Char(
        string='Customer Reference',
        compute='_compute_sale_order_info',
        store=True,
        readonly=False,
        help='Customer Reference of the linked Sales Order. '
             'Will become the Project link once the project app exists.',
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        index=True,
        ondelete='set null',
        help='For future Sales commission (Phase 2)',
    )

    # Commission calculation fields
    base_amount = fields.Float(
        string='Base Amount',
        digits=(12, 2),
        compute='_compute_base_amount',
        store=True,
        readonly=False,
        help='Sum of commissionable material costs',
    )
    rate = fields.Float(
        string='Rate (%)',
        digits=(5, 2),
        aggregator='avg',
        help='Commission rate applied',
    )
    amount = fields.Float(
        string='Commission Amount',
        digits=(12, 2),
        compute='_compute_amount',
        store=True,
        readonly=False,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Client',
        index=True,
        ondelete='set null',
        help='Client associated with this manual commission',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='scheme_id.currency_id',
        store=True,
    )

    # Status workflow
    state = fields.Selection([
        ('pending', 'Applied'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending', required=True)

    confirmed_date = fields.Datetime(
        string='Confirmed On',
        readonly=True,
    )
    confirmed_by = fields.Many2one(
        'res.users',
        string='Confirmed By',
        readonly=True,
    )
    paid_date = fields.Date(
        string='Paid Date',
        readonly=True,
    )
    paid_by = fields.Many2one(
        'res.users',
        string='Paid By',
        readonly=True,
    )
    payment_id = fields.Many2one(
        'account.payment',
        string='Payment',
        readonly=True,
        ondelete='set null',
        index=True,
    )

    amount_paid = fields.Float(
        string='Amount Paid',
        digits=(12, 2),
        compute='_compute_amount_paid',
        store=True,
    )
    amount_due = fields.Float(
        string='Amount Due',
        digits=(12, 2),
        compute='_compute_amount_paid',
        store=True,
    )

    notes = fields.Text(string='Notes')

    # Delivery tracking
    delivered = fields.Boolean(
        string='Delivered',
        compute='_compute_delivered',
        store=True,
        readonly=False,
        help='Auto-detected from Sale Order delivery status. Can be manually overridden.',
    )
    delivery_date = fields.Date(
        string='Delivery Date',
        compute='_compute_delivered',
        store=True,
        readonly=False,
    )

    # Billing
    bill_id = fields.Many2one(
        'account.move',
        string='Vendor Bill',
        readonly=True,
        ondelete='set null',
        index=True,
        help='The vendor bill this commission line was included in',
    )
    bill_state = fields.Selection([
        ('not_billed', 'Not Billed'),
        ('billed', 'Billed'),
        ('paid', 'Paid'),
    ], string='Bill Status', compute='_compute_bill_state', store=True)

    # Year lock
    year_locked = fields.Boolean(
        string='Year Locked',
        default=False,
        help='Set when the commission year is closed. Prevents further edits.',
    )

    # Material breakdown
    material_line_ids = fields.One2many(
        'vpa.commission.line.material',
        'commission_line_id',
        string='Materials',
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('vpa.commission.line') or _('New')
        return super().create(vals_list)

    @api.depends('production_id', 'production_id.sale_line_id.order_id.picking_ids.state',
                 'production_id.origin')
    def _compute_delivered(self):
        for line in self:
            # Resolve the sale order the same way the SO-name column does:
            # direct sale-line link first, otherwise match by MO origin
            # (manually linked MOs have no sale_line_id).
            sale_order = False
            production = line.production_id
            if production:
                if production.sale_line_id:
                    sale_order = production.sale_line_id.order_id
                elif production.origin:
                    sale_order = self.env['sale.order'].search(
                        [('name', '=', production.origin)], limit=1)
            if sale_order:
                done_pickings = sale_order.picking_ids.filtered(
                    lambda p: p.state == 'done' and p.picking_type_code == 'outgoing'
                )
                if done_pickings:
                    line.delivered = True
                    line.delivery_date = done_pickings[0].date_done.date() if done_pickings[0].date_done else False
                    continue
            # No delivery found: keep manual overrides, default the rest
            if not line.delivered:
                line.delivered = False
            if not line.delivery_date:
                line.delivery_date = False

    @api.depends('production_id', 'production_id.sale_line_id.order_id',
                 'production_id.sale_line_id.order_id.client_order_ref',
                 'production_id.product_id', 'production_id.origin')
    def _compute_sale_order_info(self):
        for line in self:
            sale_order = False
            if line.production_id and hasattr(line.production_id, 'sale_line_id') and line.production_id.sale_line_id:
                sale_order = line.production_id.sale_line_id.order_id
            elif line.production_id and line.production_id.origin:
                # Manually linked MOs carry the SO only in origin
                sale_order = self.env['sale.order'].search(
                    [('name', '=', line.production_id.origin)], limit=1)
            line.sale_order_name = sale_order.name if sale_order else (line.production_id.origin or False)
            line.item_name = line.production_id.product_id.name if line.production_id else False
            line.customer_ref = sale_order.client_order_ref if sale_order else False
            # Derive the client from the SO for production lines;
            # manual lines keep the client entered in the wizard.
            if sale_order:
                line.partner_id = sale_order.partner_id

    @api.depends('date')
    def _compute_date_parts(self):
        for line in self:
            if line.date:
                line.date_year = str(line.date.year)
                line.date_month = line.date.strftime('%Y-%m')
            else:
                line.date_year = False
                line.date_month = False

    @api.depends('material_line_ids.included', 'material_line_ids.amount')
    def _compute_base_amount(self):
        for line in self:
            if line.material_line_ids:
                line.base_amount = sum(
                    m.amount for m in line.material_line_ids if m.included
                )
            # If no materials (manual or sales type), leave base_amount as-is

    @api.depends('base_amount', 'rate', 'type')
    def _compute_amount(self):
        for line in self:
            if line.type == 'manual':
                # For manual lines, don't overwrite — amount is set directly
                if not line.amount:
                    line.amount = line.base_amount * line.rate / 100 if line.rate else 0.0
            else:
                line.amount = line.base_amount * line.rate / 100

    @api.depends('amount', 'state')
    def _compute_amount_paid(self):
        for line in self:
            if line.state == 'paid':
                line.amount_paid = line.amount
            else:
                line.amount_paid = 0.0
            line.amount_due = line.amount - line.amount_paid

    @api.depends('bill_id', 'bill_id.payment_state')
    def _compute_bill_state(self):
        for line in self:
            if not line.bill_id:
                line.bill_state = 'not_billed'
            elif line.bill_id.payment_state == 'paid':
                line.bill_state = 'paid'
            else:
                line.bill_state = 'billed'

    def _check_year_locked(self):
        """Raise if any selected line is year-locked."""
        locked = self.filtered(lambda l: l.year_locked)
        if locked:
            raise UserError(_(
                'Commission lines for a closed year cannot be modified: %s',
                ', '.join(locked.mapped('name'))
            ))

    def action_confirm(self):
        """Confirm commission lines - only managers can do this."""
        self._check_year_locked()
        for line in self:
            if line.state != 'pending':
                raise UserError(_('Only pending commission lines can be confirmed.'))
            line.write({
                'state': 'confirmed',
                'confirmed_date': fields.Datetime.now(),
                'confirmed_by': self.env.uid,
            })
        # Refresh the current view so approved rows drop out of filtered lists
        return {'type': 'ir.actions.client', 'tag': 'soft_reload'}

    def action_bulk_confirm(self):
        """Confirm all pending lines in the selection; skip the rest gracefully."""
        pending = self.filtered(lambda l: l.state == 'pending' and not l.year_locked)
        pending.write({
            'state': 'confirmed',
            'confirmed_date': fields.Datetime.now(),
            'confirmed_by': self.env.uid,
        })
        skipped = len(self) - len(pending)
        msg = _('%d commission line(s) confirmed.') % len(pending)
        if skipped:
            msg += _(' %d skipped (not pending or year-locked).') % skipped
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': _('Confirm'), 'message': msg,
                       'type': 'success', 'sticky': False,
                       'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'}},
        }

    def action_cancel(self):
        """Cancel commission lines."""
        self._check_year_locked()
        for line in self:
            if line.state == 'paid':
                raise UserError(_('Paid commission lines cannot be cancelled. Reset to pending first.'))
            line.write({'state': 'cancelled'})
        return {'type': 'ir.actions.client', 'tag': 'soft_reload'}

    def action_reset_to_pending(self):
        """Reset confirmed, paid, or cancelled lines back to pending."""
        for line in self:
            if line.state not in ('confirmed', 'paid', 'cancelled'):
                raise UserError(_('Only confirmed, paid, or cancelled commission lines can be reset to pending.'))
            line.write({
                'state': 'pending',
                'confirmed_date': False,
                'confirmed_by': False,
                'paid_date': False,
                'paid_by': False,
                'payment_id': False,
            })

    def action_view_bill(self):
        """Open the related vendor bill."""
        self.ensure_one()
        if not self.bill_id:
            raise UserError(_('No vendor bill linked to this commission line.'))
        return {
            'name': _('Vendor Bill'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.bill_id.id,
        }

    def action_adjust_materials(self):
        """Open the Adjust Materials wizard."""
        self.ensure_one()
        if self.state in ('paid', 'cancelled'):
            raise UserError(_('Cannot adjust materials on a paid or cancelled commission line.'))
        if not self.material_line_ids:
            raise UserError(_('No materials to adjust.'))

        wizard = self.env['vpa.adjust.materials.wizard'].create({
            'commission_line_id': self.id,
            'line_ids': [(0, 0, {
                'material_line_id': m.id,
                'included': m.included,
            }) for m in self.material_line_ids],
        })
        return {
            'name': _('Adjust Materials'),
            'type': 'ir.actions.act_window',
            'res_model': 'vpa.adjust.materials.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }

    def action_view_production(self):
        """Open the related manufacturing order."""
        self.ensure_one()
        if not self.production_id:
            raise UserError(_('No manufacturing order linked to this commission line.'))
        return {
            'name': _('Manufacturing Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': self.production_id.id,
        }

    @api.model
    def action_open_commission_payments(self):
        """Open all commission payments: line-linked, year-linked and bill-matched."""
        line_payment_ids = self.search([
            ('payment_id', '!=', False),
        ]).mapped('payment_id').ids
        year_payments = self.env['account.payment'].search([
            ('commission_year_id', '!=', False),
        ])
        bill_payments = self.env['account.move'].search([
            ('commission_year_id', '!=', False),
        ]).mapped('matched_payment_ids')
        payment_ids = list(set(line_payment_ids) | set(year_payments.ids) | set(bill_payments.ids))
        list_view = self.env.ref('vpa_sales_commission.view_account_payment_list_commission')
        return {
            'name': _('Commission Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'views': [(list_view.id, 'list'), (False, 'form')],
            'domain': [('id', 'in', payment_ids)],
            'context': {'create': False},
        }


class VpaCommissionLineMaterial(models.Model):
    _name = 'vpa.commission.line.material'
    _description = 'Commission Line Material'
    _order = 'id'

    commission_line_id = fields.Many2one(
        'vpa.commission.line',
        string='Commission Line',
        required=True,
        ondelete='cascade',
        index=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        readonly=True,
    )
    quantity = fields.Float(
        string='Quantity',
        digits=(12, 4),
        readonly=True,
    )
    unit_cost = fields.Float(
        string='Unit Cost',
        digits=(12, 2),
        readonly=True,
    )
    amount = fields.Float(
        string='Total Cost',
        digits=(12, 2),
        readonly=True,
    )
    included = fields.Boolean(
        string='Included',
    )
