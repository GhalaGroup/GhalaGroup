# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BomCopyFromWizard(models.TransientModel):
    """Wizard to copy BOM lines from a previous BOM for the same product.

    Opens a filtered list of previous BOMs (non-Master) for the same product,
    allowing the user to select one and copy its component lines into the
    current BOM.
    """
    _name = 'vpa.bom.copy.from.wizard'
    _description = 'Copy BOM Lines from Previous BOM'

    target_bom_id = fields.Many2one(
        'mrp.bom',
        string='Current BOM',
        required=True,
        readonly=True,
        help="The BOM that will receive the copied lines.",
    )
    source_bom_id = fields.Many2one(
        'mrp.bom',
        string='Copy from BOM',
        required=True,
        help="Select a previous BOM to copy lines from.",
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product',
        readonly=True,
        help="Product template used to filter available BOMs.",
    )
    replace_lines = fields.Boolean(
        string='Replace existing lines',
        default=True,
        help="If checked, existing BOM lines will be removed before copying. "
             "If unchecked, copied lines will be added to existing ones.",
    )

    # Preview fields
    source_bom_line_count = fields.Integer(
        string='Lines to Copy',
        compute='_compute_source_info',
    )
    source_bom_reference = fields.Char(
        string='Source Reference',
        compute='_compute_source_info',
    )
    source_bom_date = fields.Datetime(
        string='Source Created Date',
        compute='_compute_source_info',
    )

    @api.depends('source_bom_id')
    def _compute_source_info(self):
        """Compute preview info from the selected source BOM."""
        for wiz in self:
            if wiz.source_bom_id:
                wiz.source_bom_line_count = len(
                    wiz.source_bom_id.bom_line_ids.filtered(lambda l: not l.display_type)
                )
                wiz.source_bom_reference = wiz.source_bom_id.code_with_revision or wiz.source_bom_id.code or ''
                wiz.source_bom_date = wiz.source_bom_id.created_date
            else:
                wiz.source_bom_line_count = 0
                wiz.source_bom_reference = ''
                wiz.source_bom_date = False

    @api.model
    def default_get(self, fields_list):
        """Set defaults from the active BOM context."""
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            bom = self.env['mrp.bom'].browse(active_id)
            if bom.exists():
                res['target_bom_id'] = bom.id
                res['product_tmpl_id'] = bom.product_tmpl_id.id
        return res

    def action_copy_lines(self):
        """Copy BOM lines from the selected source BOM into the target BOM."""
        self.ensure_one()

        if not self.source_bom_id:
            raise UserError(_("Please select a BOM to copy from."))

        if self.source_bom_id.id == self.target_bom_id.id:
            raise UserError(_("Cannot copy from the same BOM."))

        target = self.target_bom_id
        source = self.source_bom_id

        # Safety check: never modify a Master BOM through this wizard
        if target.is_master_bom:
            raise UserError(
                _("Cannot copy lines into a Master BOM. "
                  "This wizard is for standard/order-specific BOMs only.")
            )

        # Track removed lines for audit trail
        removed_lines_info = []
        if self.replace_lines and target.bom_line_ids:
            for line in target.bom_line_ids:
                if line.display_type:
                    continue  # Skip sections/notes in audit
                name = line.product_id.display_name if line.product_id else (
                    line.bom_category_id.display_name if line.bom_category_id else 'Unknown'
                )
                removed_lines_info.append(f"{name} x {line.product_qty}")
            target.bom_line_ids.unlink()

        # Copy lines from source BOM and track for audit
        copied_lines_info = []
        for line in source.bom_line_ids:
            vals = {
                'bom_id': target.id,
                'sequence': line.sequence,
            }

            if line.display_type:
                # Section or note line
                vals.update({
                    'display_type': line.display_type,
                    'name': line.name,
                    'product_id': False,
                    'product_qty': 0,
                })
            else:
                # Regular component line
                vals.update({
                    'product_id': line.product_id.id if line.product_id else False,
                    'product_qty': line.product_qty,
                    'product_uom_id': line.product_uom_id.id if line.product_uom_id else False,
                    'bom_category_id': line.bom_category_id.id if line.bom_category_id else False,
                    'line_description': line.line_description,
                })
                # Track for audit
                name = line.product_id.display_name if line.product_id else (
                    line.bom_category_id.display_name if line.bom_category_id else 'Unknown'
                )
                copied_lines_info.append(f"{name} x {line.product_qty}")

            self.env['mrp.bom.line'].create(vals)

        # Update the target BOM's created date to now
        target.write({
            'created_date': fields.Datetime.now(),
        })

        # Log in chatter for full traceability
        source_ref = source.code_with_revision or source.display_name
        body_parts = [
            f"<strong>Copied BOM lines from:</strong> {source_ref}<br/>"
        ]
        if self.replace_lines and removed_lines_info:
            body_parts.append(
                f"<strong>Removed {len(removed_lines_info)} existing line(s):</strong><br/>"
                + "<br/>".join(f"&nbsp;&nbsp;- {l}" for l in removed_lines_info)
                + "<br/>"
            )
        body_parts.append(
            f"<strong>Copied {len(copied_lines_info)} line(s):</strong><br/>"
            + "<br/>".join(f"&nbsp;&nbsp;+ {l}" for l in copied_lines_info)
        )

        target.message_post(
            body=Markup("".join(body_parts)),
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('BOM Lines Copied'),
                'message': _('Copied %d lines from %s') % (
                    len(copied_lines_info),
                    source_ref,
                ),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
