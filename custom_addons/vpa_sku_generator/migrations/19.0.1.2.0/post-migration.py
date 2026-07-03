# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
#
# Post-migration for 19.0.1.2.0
# Reconcile every category SKU sequence with the real highest SKU already in use.
#
# Background: a previous change renamed the sequence code format (short_name ->
# full hierarchy path). Existing sequences kept the OLD code, so new products
# triggered creation of a BRAND NEW sequence starting near 1 -> duplicate SKUs
# (e.g. UDI/OFC/00003 while 78 chairs already existed). This migration heals every
# sequence so its next number is past the highest existing SKU for its prefix.

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})

    Category = env['product.category']
    IrSequence = env['ir.sequence'].sudo()

    categories = Category.search([('short_name', '!=', False)])
    healed = 0
    for cat in categories:
        try:
            sequence_code = cat._get_sequence_code()
        except Exception:
            sequence_code = False
        if not sequence_code:
            continue

        company_id = cat.company_id.id or env.company.id
        real_max = cat._get_max_sku_number_from_products()
        if real_max <= 0:
            continue
        safe_next = real_max + 1

        seq = IrSequence.search([
            ('code', '=', sequence_code),
            ('company_id', '=', company_id),
        ], limit=1)

        if not seq:
            # No sequence under the current (new) code yet: create it seeded correctly.
            parents = env['product.category'].search(
                [('id', 'parent_of', cat.id)], order='id asc')
            full_path = "/".join(parents.mapped('short_name'))
            IrSequence.create({
                'name': f"Product SKU Sequence: {full_path}",
                'code': sequence_code,
                'padding': 5,
                'number_next': safe_next,
                'number_increment': 1,
                'company_id': company_id,
            })
            healed += 1
            _logger.info("SKU migration: created sequence %s seeded at %s (cat %s)",
                         sequence_code, safe_next, cat.complete_name)
        elif seq.number_next_actual < safe_next:
            seq.write({'number_next': safe_next})
            healed += 1
            _logger.info("SKU migration: healed sequence %s -> next %s (cat %s, was behind real max %s)",
                         sequence_code, safe_next, cat.complete_name, real_max)

    _logger.info("SKU migration 19.0.1.2.0 complete: %s sequence(s) reconciled.", healed)
