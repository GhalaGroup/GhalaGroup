# -*- coding: utf-8 -*-
from markupsafe import Markup
from odoo import models, api, _
from odoo.tools import html_escape


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

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
                    sale_order.message_post(
                        body=body,
                        message_type='notification',
                        subtype_id=note_subtype_id
                    )

        return result
