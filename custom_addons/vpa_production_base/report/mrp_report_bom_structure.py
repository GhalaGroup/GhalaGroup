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
        # Check if this is a template line (has category but no product)
        if bom_line.bom_category_id and not bom_line.product_id:
            # Return custom data structure for template lines
            from odoo import _
            # Build name with description if available
            name_parts = [bom_line.bom_category_id.name]
            if bom_line.line_description:
                name_parts.append(f"({bom_line.line_description})")
            display_name = " ".join(name_parts)

            return {
                'type': 'template',  # Mark as template line
                'index': index,
                'product_id': False,
                'product': self.env['product.product'],  # Empty recordset
                'link_id': f'line_{bom_line.id}',
                'link_model': 'mrp.bom.line',
                'name': display_name,
                'category_code': bom_line.bom_category_id.code or '',
                'quantity': line_quantity,
                'uom': bom_line.product_uom_id,
                'uom_name': bom_line.product_uom_id.name if bom_line.product_uom_id else '',
                'prod_cost': 0.0,
                'bom_cost': 0.0,
                'route_name': '',
                'route_detail': _('To be selected during manufacturing'),
                'lead_time': False,
                'visible': True,
                'quantity_available': 0.0,
                'quantity_on_hand': 0.0,
                'quantity_forecasted': 0.0,
                'free_to_manufacture_qty': 0.0,
                'producible_qty': 0.0,
                'availability_display': _('Template'),
                'availability_state': 'template',
                'stock_avail_state': 'available',  # Template lines are always "available"
                'base_bom_line_qty': line_quantity,
                'is_storable': False,
                'components_available': True,
                'has_attachments': False,  # Template lines have no attachments
                'description': bom_line.line_description or '',
                'level': level,
            }

        # For standard lines with products, use parent logic
        return super()._get_component_data(parent_bom, parent_product, warehouse, bom_line, line_quantity, level, index, product_info, ignore_stock)
