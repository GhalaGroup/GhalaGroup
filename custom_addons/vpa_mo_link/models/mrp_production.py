# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.tools import html_escape


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _post_run_manufacture(self, post_production_values):
        """
        Override to post detailed messages when MO is created from Sales Order.

        Adds comprehensive information including:
        - Manufacturing Order number with link
        - Product name and quantity
        - Source document (Sales Order) with link
        - BOM reference if available
        """
        # Call parent method first
        result = super()._post_run_manufacture(post_production_values)

        # Post detailed message for each production created from SO
        note_subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')

        for production in self:
            # Only post if created from a Sales Order (origin starts with 'S')
            if production.origin and production.origin.startswith('S'):
                # Find the related Sales Order
                sale_order = self.env['sale.order'].search([
                    ('name', '=', production.origin)
                ], limit=1)

                # Build detailed message
                message_parts = []

                # MO details
                mo_link = f'<a href="/odoo/mrp.production/{production.id}">{html_escape(production.name)}</a>'
                message_parts.append(f"<strong>Manufacturing Order:</strong> {mo_link}")

                # Product details
                product_name = html_escape(production.product_id.display_name)
                qty = production.product_qty
                uom = html_escape(production.product_uom_id.name)
                message_parts.append(f"<strong>Product:</strong> {product_name}")
                message_parts.append(f"<strong>Quantity:</strong> {qty} {uom}")

                # BOM details
                if production.bom_id:
                    bom_name = html_escape(production.bom_id.display_name or production.bom_id.code or f"BOM #{production.bom_id.id}")
                    message_parts.append(f"<strong>Bill of Materials:</strong> {bom_name}")
                else:
                    message_parts.append("<strong>Bill of Materials:</strong> <em>Not set - please configure before confirming</em>")

                # Source document
                if sale_order:
                    so_link = f'<a href="/odoo/sale.order/{sale_order.id}">{html_escape(sale_order.name)}</a>'
                    message_parts.append(f"<strong>Source:</strong> {so_link}")
                else:
                    message_parts.append(f"<strong>Source:</strong> {html_escape(production.origin)}")

                # State info
                message_parts.append(f"<strong>State:</strong> Draft (awaiting confirmation)")

                # Combine message
                body = "<br/>".join(message_parts)

                # Post on the MO
                production.message_post(
                    body=body,
                    message_type='comment',
                    subtype_id=note_subtype_id
                )

                # Also post on the Sales Order if found
                if sale_order:
                    so_message_parts = []
                    so_message_parts.append(f"<strong>Manufacturing Order Created:</strong> {mo_link}")
                    so_message_parts.append(f"<strong>Product:</strong> {product_name}")
                    so_message_parts.append(f"<strong>Quantity:</strong> {qty} {uom}")
                    if production.bom_id:
                        so_message_parts.append(f"<strong>BOM:</strong> {bom_name}")
                    so_message_parts.append(f"<strong>State:</strong> Draft")

                    so_body = "<br/>".join(so_message_parts)
                    sale_order.message_post(
                        body=so_body,
                        message_type='comment',
                        subtype_id=note_subtype_id
                    )

        return result
