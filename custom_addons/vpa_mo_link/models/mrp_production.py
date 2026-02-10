# -*- coding: utf-8 -*-
from markupsafe import Markup
from odoo import models, api, fields, _
from odoo.tools import html_escape


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    lot_reference = fields.Char(
        string='Lot Reference',
        help="Reference for production lots (e.g., 'Lot 1/3', 'Lot 2/3')",
    )

    def action_split_mo(self):
        """Open wizard to split this MO into multiple lots."""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Split Manufacturing Order'),
            'res_model': 'vpa.mo.split.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_production_id': self.id,
            },
        }

    @api.depends('bom_id')
    def _compute_product_qty(self):
        """
        Override to preserve explicitly set product_qty when creating MOs.

        Standard Odoo 19 behavior: When a BOM is assigned, the MO's product_qty
        is automatically set to the BOM's product_qty. This causes issues when
        creating MOs from Sales Orders where the quantity should match the SO line,
        not the BOM default.

        This override preserves the product_qty if:
        1. It was explicitly set during creation (in context)
        2. The MO is being created (not modified)
        """
        for production in self:
            if production.state != 'draft':
                continue

            # Check if quantity was explicitly provided via context
            # (used by server actions and programmatic creation)
            explicit_qty = self.env.context.get('vpa_explicit_product_qty')
            if explicit_qty and not production._origin.id:
                # New record with explicit quantity - preserve it
                production.product_qty = explicit_qty
            elif production.bom_id and production._origin.bom_id != production.bom_id:
                # BOM changed - use BOM's quantity (standard behavior)
                production.product_qty = production.bom_id.product_qty
            elif not production.bom_id:
                # No BOM - default to 1
                production.product_qty = 1.0

    def _post_run_manufacture(self, post_production_values):
        """
        Override to post detailed messages when MO is created from Sales Order.

        Posts a clean one-line message like:
        Auto-created MO P01M/MO/00511 for [Product] (Qty: 1.64) - with BOM
        """
        # Call parent method first
        result = super()._post_run_manufacture(post_production_values)

        # Post message for each production created from SO
        note_subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')

        for production in self:
            # Only post if created from a Sales Order (origin starts with 'S')
            if production.origin and production.origin.startswith('S'):
                # Find the related Sales Order
                sale_order = self.env['sale.order'].search([
                    ('name', '=', production.origin)
                ], limit=1)

                # Build clean one-line message
                mo_link = f'<a href="/odoo/mrp.production/{production.id}">{html_escape(production.name)}</a>'
                product_name = html_escape(production.product_id.display_name)
                qty = production.product_qty
                bom_status = "with BOM" if production.bom_id else "NO BOM"

                # Format: Auto-created MO P01M/MO/00511 for [Product] (Qty: 1.64) - with BOM
                body = Markup(f"Auto-created MO {mo_link} for {product_name} (Qty: {qty}) - {bom_status}")

                # Post on the Sales Order if found
                if sale_order:
                    # Try to find OdooBot/Odoo Agent partner for author
                    odoo_agent = self.env['res.partner'].sudo().search([
                        ('name', 'ilike', 'odoo agent')
                    ], limit=1)
                    author = odoo_agent.id if odoo_agent else False

                    sale_order.sudo().message_post(
                        body=body,
                        message_type='notification',
                        subtype_id=note_subtype_id,
                        author_id=author
                    )

        return result
