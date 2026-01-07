# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from markupsafe import Markup
from odoo import api, fields, models, _


class MrpBomLine(models.Model):
    """Extend mrp.bom.line with audit trail for BOM line changes.

    All key field changes are logged to the parent BOM's chatter
    for full traceability of who changed what and when.
    """
    _inherit = 'mrp.bom.line'

    # =========================================================================
    # AUDIT TRAIL - Track changes to parent BOM's chatter
    # =========================================================================
    def _get_tracked_fields(self):
        """Return dict of fields to track with their display labels."""
        return {
            'bom_category_id': 'Category',
            'product_id': 'Product',
            'product_qty': 'Quantity',
            'product_uom_id': 'UoM',
            'line_description': 'Description',
        }

    def _format_field_value(self, field_name, value):
        """Format field value for display in tracking message."""
        if value is False or value is None:
            return _("(empty)")
        if field_name in ('bom_category_id', 'product_id', 'product_uom_id'):
            # Many2one fields - get display name
            return value.display_name if value else _("(empty)")
        if field_name == 'product_qty':
            return str(value)
        return str(value) if value else _("(empty)")

    def unlink(self):
        """Log line deletions to parent BOM's chatter before deleting."""
        # Capture line info before deletion
        lines_by_bom = {}
        for line in self:
            if line.bom_id and not line.display_type:  # Skip sections/notes
                bom_id = line.bom_id.id
                if bom_id not in lines_by_bom:
                    lines_by_bom[bom_id] = {'bom': line.bom_id, 'lines': []}

                # Build line description
                if line.product_id:
                    line_desc = line.product_id.display_name
                elif line.bom_category_id:
                    line_desc = f"[{line.bom_category_id.name}] {line.line_description or ''}"
                else:
                    line_desc = _("Line")

                qty_info = f"{line.product_qty} {line.product_uom_id.name}" if line.product_uom_id else str(line.product_qty)
                lines_by_bom[bom_id]['lines'].append(f"{line_desc} ({qty_info})")

        # Perform deletion
        result = super().unlink()

        # Post messages to BOMs (after successful deletion)
        for bom_id, data in lines_by_bom.items():
            bom = data['bom']
            if bom.exists():
                msg = "<strong>BOM Lines Removed:</strong><ul>"
                for desc in data['lines']:
                    msg += f"<li>{desc}</li>"
                msg += "</ul>"
                bom.message_post(body=Markup(msg), message_type='notification')

        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Log line additions to BOM chatter."""
        lines = super().create(vals_list)

        # Log new lines to parent BOM's chatter
        lines_by_bom = {}
        for line in lines:
            if line.bom_id and not line.display_type:  # Skip sections/notes
                bom_id = line.bom_id.id
                if bom_id not in lines_by_bom:
                    lines_by_bom[bom_id] = []

                # Build line description
                if line.product_id:
                    line_desc = line.product_id.display_name
                elif line.bom_category_id:
                    line_desc = f"[{line.bom_category_id.name}] {line.line_description or ''}"
                else:
                    line_desc = _("New Line")

                qty_info = f"{line.product_qty} {line.product_uom_id.name}" if line.product_uom_id else str(line.product_qty)
                lines_by_bom[bom_id].append(f"{line_desc} ({qty_info})")

        # Post messages to BOMs
        for bom_id, line_descs in lines_by_bom.items():
            bom = self.env['mrp.bom'].browse(bom_id)
            if bom.exists():
                msg = "<strong>BOM Lines Added:</strong><ul>"
                for desc in line_descs:
                    msg += f"<li>{desc}</li>"
                msg += "</ul>"
                bom.message_post(body=Markup(msg), message_type='notification')

        return lines

    def write(self, vals):
        """Track changes and log to BOM chatter."""
        # Capture old values for tracking BEFORE the write
        tracked_fields = self._get_tracked_fields()
        changes_by_bom = {}  # {bom_id: [(line, field, old_val, new_val), ...]}

        for line in self:
            if not line.bom_id:
                continue
            bom_id = line.bom_id.id
            if bom_id not in changes_by_bom:
                changes_by_bom[bom_id] = []

            for field_name, label in tracked_fields.items():
                if field_name in vals:
                    old_value = getattr(line, field_name)
                    new_value = vals[field_name]

                    # For Many2one fields, get the record for new value
                    if field_name in ('bom_category_id', 'product_id', 'product_uom_id') and new_value:
                        field_obj = self._fields[field_name]
                        new_record = self.env[field_obj.comodel_name].browse(new_value)
                    else:
                        new_record = new_value

                    # Only track if value actually changed
                    old_formatted = line._format_field_value(field_name, old_value)
                    new_formatted = line._format_field_value(field_name, new_record)

                    if old_formatted != new_formatted:
                        line_ref = line.product_id.display_name if line.product_id else (
                            line.line_description or line.bom_category_id.name if line.bom_category_id else f"Line #{line.id}"
                        )
                        changes_by_bom[bom_id].append({
                            'line_ref': line_ref,
                            'field_label': label,
                            'old_value': old_formatted,
                            'new_value': new_formatted,
                        })

        # Perform the actual write
        result = super().write(vals)

        # Log changes to parent BOM's chatter
        for bom_id, changes in changes_by_bom.items():
            if changes:
                bom = self.env['mrp.bom'].browse(bom_id)
                if bom.exists():
                    # Build message body
                    msg_lines = ["<strong>BOM Line Changes:</strong><ul>"]
                    for change in changes:
                        msg_lines.append(
                            f"<li><b>{change['line_ref']}</b>: {change['field_label']} "
                            f"changed from <i>{change['old_value']}</i> to <i>{change['new_value']}</i></li>"
                        )
                    msg_lines.append("</ul>")
                    bom.message_post(body=Markup(''.join(msg_lines)), message_type='notification')

        return result
