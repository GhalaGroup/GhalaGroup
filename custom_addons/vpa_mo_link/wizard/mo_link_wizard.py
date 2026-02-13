# -*- coding: utf-8 -*-
from markupsafe import Markup
from odoo import models, fields, api


class MoLinkWizard(models.TransientModel):
    _name = 'vpa.mo.link.wizard'
    _description = 'Link MO to Sales Order'

    production_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing Order',
        required=True,
        readonly=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        required=True,
        domain=[('state', 'not in', ['cancel'])],
    )

    def action_link(self):
        """Link the MO to the selected Sales Order"""
        self.ensure_one()
        mo = self.production_id
        so = self.sale_order_id

        # Set origin to SO name
        mo.write({'origin': so.name})

        # Link MO finished moves to pending delivery moves (MTO chain)
        pending_pickings = self.env['stock.picking'].search([
            ('origin', '=', so.name),
            ('state', 'not in', ('done', 'cancel')),
            ('picking_type_code', '=', 'outgoing'),
        ])
        for picking in pending_pickings:
            for finished_move in mo.move_finished_ids:
                delivery_move = picking.move_ids.filtered(
                    lambda m, p=finished_move.product_id: m.product_id == p and m.state not in ('done', 'cancel')
                )
                if delivery_move and finished_move:
                    delivery_move[0].write({'move_orig_ids': [(4, finished_move.id)]})
                    finished_move.write({'move_dest_ids': [(4, delivery_move[0].id)]})

        # Post messages
        so_link = Markup("<a href='#id=%s&model=sale.order'>%s</a>") % (so.id, so.name)
        mo.message_post(body=Markup("Linked to Sales Order %s") % so_link)

        mo_link = Markup("<a href='#id=%s&model=mrp.production'>%s</a>") % (mo.id, mo.name)
        so.message_post(body=Markup("Linked Manufacturing Order %s") % mo_link)

        # Invalidate SO cache to refresh smart button
        so.invalidate_recordset(['mrp_production_ids', 'mrp_production_count'])

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Linked to SO',
                'message': f"MO {mo.name} linked to {so.name}",
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
            }
        }
