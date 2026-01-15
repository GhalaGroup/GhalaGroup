# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, models


class MrpBomLine(models.Model):
    """Extend mrp.bom.line to handle template lines in reports."""
    _inherit = 'mrp.bom.line'

    def _skip_bom_line(self, product, never_attribute_values=False):
        """Check if this BOM line should be skipped.

        Template lines (lines without products) should NOT be skipped.
        """
        # DON'T skip template lines - they should be shown in reports
        # Check parent logic for other skip conditions
        return super()._skip_bom_line(product, never_attribute_values)


class ReportBomStructure(models.AbstractModel):
    """Extend BOM structure report to handle template lines."""
    _inherit = 'report.mrp.report_bom_structure'

    def _get_bom_data(self, bom, warehouse, product=False, line_qty=False, level=0):
        """Override to handle template lines and fix reference display."""
        result = super()._get_bom_data(bom, warehouse, product, line_qty, level)

        # Fix the reference to show revision (used by both PDF report and JS overview)
        if result and bom:
            if hasattr(bom, 'code_with_revision') and bom.code_with_revision:
                result['bom_code'] = bom.code_with_revision
                if 'code' in result:
                    result['code'] = bom.code_with_revision

        return result

    def _get_component_data(self, parent_bom, parent_product, warehouse, bom_line, line_quantity, level, index, product_info, ignore_stock=False):
        """Override to handle template lines (lines without products)."""
        # Check if this is a template line (no product assigned)
        # This covers both: lines with category (active Master BOM) and lines without category (pending conversion)
        if not bom_line.product_id:
            # Return custom data structure for template lines
            from odoo import _
            # Build name with description if available
            name_parts = []
            if bom_line.bom_category_id:
                name_parts.append(bom_line.bom_category_id.name)
            elif bom_line.original_product_id:
                # Pending conversion: show original product name
                name_parts.append(f"[Pending] {bom_line.original_product_id.name}")
            else:
                name_parts.append(_("Template Line"))
            if bom_line.line_description:
                name_parts.append(f"({bom_line.line_description})")
            display_name = " ".join(name_parts)

            # Return complete data structure matching what Odoo expects
            currency = self.env.company.currency_id
            return {
                # Basic info
                'type': 'template',
                'index': index,
                'bom_id': False,
                'bom': False,
                'product_id': False,
                'product': self.env['product.product'],
                'link_id': f'line_{bom_line.id}',
                'link_model': 'mrp.bom.line',
                'name': display_name,
                'code': bom_line.bom_category_id.code if bom_line.bom_category_id else '',
                'level': level,
                'parent_id': False,

                # Quantities
                'quantity': line_quantity,
                'base_bom_line_qty': line_quantity,
                'uom': bom_line.product_uom_id,
                'uom_name': bom_line.product_uom_id.name if bom_line.product_uom_id else _('Units'),

                # Costs
                'prod_cost': 0.0,
                'bom_cost': 0.0,
                'currency_id': currency.id,
                'currency': currency,

                # Availability - all fields needed by _format_availability and _merge_components
                'quantity_available': 0.0,
                'quantity_on_hand': 0.0,
                'quantity_forecasted': 0.0,
                'free_to_manufacture_qty': 0.0,
                'producible_qty': 0.0,
                'availability_display': _('Template - Select during MO'),
                'availability_state': 'available',
                'availability_delay': 0,
                'resupply_avail_delay': 0,
                'stock_avail_state': 'available',

                # Route info
                'route_name': '',
                'route_detail': '',
                'route_type': 'manufacture',
                'lead_time': 0,

                # Flags
                'visible': True,
                'is_storable': False,
                'phantom': False,
                'components_available': True,
                'has_attachments': False,

                # Components
                'components': [],

                # Description
                'description': bom_line.line_description or '',
            }

        # For standard lines with products, use parent logic
        return super()._get_component_data(parent_bom, parent_product, warehouse, bom_line, line_quantity, level, index, product_info, ignore_stock)
