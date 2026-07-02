# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

import re
import logging
from markupsafe import Markup
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SkuAuditWizard(models.TransientModel):
    """SKU Audit - scan products for SKU integrity issues and fix them safely.

    Detects:
      - mismatch       : single-variant product whose variant Internal Reference
                         differs from its template (the same item showing two codes)
      - duplicate      : the same Internal Reference used by more than one variant
      - missing        : active storable product with no Internal Reference
      - variant_irregular: real multi-variant product not following the base/-NNN convention

    Fix actions (chosen on the wizard):
      - Align variant to template (safe, targeted)
      - Regenerate from category sequence (re-number)
    Both can push freed numbers to the recycle pool and always post a chatter note.
    """
    _name = 'sku.audit.wizard'
    _description = 'SKU Audit'

    state = fields.Selection([
        ('draft', 'Configure'),
        ('preview', 'Review Findings'),
        ('done', 'Done'),
    ], default='draft')

    # ---- what to scan for ----
    check_mismatch = fields.Boolean(
        string="Template / Variant Code Mismatch", default=True,
        help="Single-variant products where the variant Internal Reference differs from the template.")
    check_duplicate = fields.Boolean(
        string="Duplicate Codes", default=True,
        help="The same Internal Reference assigned to more than one product variant.")
    check_missing = fields.Boolean(
        string="Missing Codes", default=True,
        help="Active storable products that have no Internal Reference.")
    check_variant_irregular = fields.Boolean(
        string="Multi-Variant Irregularities", default=False,
        help="Real multi-variant products not following the base/-NNN suffix convention "
             "(informational; auto-fix is not recommended).")

    # ---- how to fix ----
    fix_method = fields.Selection([
        ('align', 'Align variant to template (recommended)'),
        ('regenerate', 'Regenerate from category sequence'),
    ], string="Fix Method", default='align', required=True,
        help="Align: set the variant code equal to its template code (safe, targeted).\n"
             "Regenerate: assign a fresh number from the category sequence.")
    recycle_freed = fields.Boolean(
        string="Send Freed Codes to Recycle Pool", default=True,
        help="Add released Internal References to the SKU Recycle Pool for reuse.")
    post_chatter = fields.Boolean(
        string="Post Traceability Note", default=True,
        help="Log the old -> new Internal Reference and date on each changed product (chatter).")

    company_id = fields.Many2one('res.company', string="Company",
                                 help="Limit the audit to one company. Leave empty to scan all companies you can access.")

    line_ids = fields.One2many('sku.audit.wizard.line', 'wizard_id', string="Findings")

    # ---- stats ----
    total_found = fields.Integer(compute='_compute_stats')
    total_fixable = fields.Integer(compute='_compute_stats')
    total_collision = fields.Integer(compute='_compute_stats')

    @api.depends('line_ids', 'line_ids.fixable')
    def _compute_stats(self):
        for w in self:
            w.total_found = len(w.line_ids)
            w.total_fixable = len(w.line_ids.filtered(lambda l: l.fixable and l.to_fix))
            w.total_collision = len(w.line_ids.filtered(lambda l: not l.fixable))

    # ------------------------------------------------------------------
    # SCAN
    # ------------------------------------------------------------------
    def action_scan(self):
        self.ensure_one()
        self.line_ids.unlink()

        # Safety: if no check is selected (e.g. checkbox values not persisted),
        # scan for everything rather than silently returning zero findings.
        if not any([self.check_mismatch, self.check_duplicate,
                    self.check_missing, self.check_variant_irregular]):
            self.write({
                'check_mismatch': True, 'check_duplicate': True,
                'check_missing': True, 'check_variant_irregular': False,
            })

        Tmpl = self.env['product.template'].with_context(active_test=False)
        Prod = self.env['product.product'].with_context(active_test=False)

        domain = []
        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))

        Line = self.env['sku.audit.wizard.line']
        vals_list = []

        # --- duplicates (computed once, by code) ---
        # dup_keeper maps a duplicated code -> the variant id that KEEPS it (lowest id,
        # i.e. created first). All other variants sharing that code are fixable.
        dup_keeper = {}
        if self.check_duplicate:
            self.env.cr.execute("""
                SELECT default_code, min(id) FROM product_product
                WHERE default_code IS NOT NULL AND default_code <> ''
                GROUP BY default_code HAVING count(*) > 1
            """)
            dup_keeper = {code: keeper_id for code, keeper_id in self.env.cr.fetchall()}

        for t in Tmpl.search(domain):
            variants = t.product_variant_ids
            tc = t.default_code or ''
            company = t.company_id.name if t.company_id else 'Shared'

            if len(variants) == 1:
                v = variants
                vc = v.default_code or ''
                # mismatch
                if self.check_mismatch and tc and vc and tc != vc:
                    collision = bool(Prod.search([('default_code', '=', tc), ('id', '!=', v.id)], limit=1))
                    vals_list.append({
                        'issue_type': 'mismatch',
                        'template_id': t.id,
                        'variant_id': v.id,
                        'product_name': t.name,
                        'company_name': company,
                        'current_code': vc,
                        'template_code': tc,
                        'proposed_code': tc if not collision else False,
                        'fixable': not collision,
                        'note': 'Template code already used by another product' if collision else '',
                    })
                # missing
                if self.check_missing and not tc and not vc and t.active and v.is_storable:
                    vals_list.append({
                        'issue_type': 'missing',
                        'template_id': t.id, 'variant_id': v.id,
                        'product_name': t.name, 'company_name': company,
                        'current_code': '', 'template_code': '',
                        'proposed_code': False, 'fixable': True,
                        'note': 'Will receive a fresh code from category sequence',
                    })
            else:
                # multi-variant irregularities (informational)
                if self.check_variant_irregular and t.attribute_line_ids:
                    codes = [v.default_code or '' for v in variants]
                    bases = {re.sub(r'-\d+$', '', c) for c in codes if c}
                    ok = tc and bases == {tc} and all(re.search(r'-\d+$', c) for c in codes)
                    if not ok:
                        vals_list.append({
                            'issue_type': 'variant_irregular',
                            'template_id': t.id, 'variant_id': False,
                            'product_name': t.name, 'company_name': company,
                            'current_code': ', '.join(c for c in codes if c)[:60],
                            'template_code': tc,
                            'proposed_code': False, 'fixable': False,
                            'to_fix': False,
                            'note': 'Real variants - review manually (auto-fix not recommended)',
                        })

            # duplicates per variant
            if self.check_duplicate:
                for v in variants:
                    if v.default_code and v.default_code in dup_keeper:
                        is_keeper = (v.id == dup_keeper[v.default_code])
                        vals_list.append({
                            'issue_type': 'duplicate',
                            'template_id': t.id, 'variant_id': v.id,
                            'product_name': t.name, 'company_name': company,
                            'current_code': v.default_code, 'template_code': tc,
                            # keeper retains the code (not fixed); the others get a fresh code
                            'proposed_code': False if is_keeper else _('(new from sequence)'),
                            'fixable': not is_keeper,
                            'to_fix': not is_keeper,
                            'note': _('Keeps this code (created first)') if is_keeper
                                    else _('Duplicate - will get a fresh code from category sequence'),
                        })

        # Respect SKU locks: a locked product was deliberately frozen, so it must
        # NOT be auto-fixed. Mark any finding on a locked template as not fixable.
        locked_tmpl_ids = set(self.env['product.template'].search([
            ('id', 'in', [v['template_id'] for v in vals_list if v.get('template_id')]),
            ('sku_locked', '=', True),
        ]).ids)
        locked_count = 0
        for v in vals_list:
            if v.get('template_id') in locked_tmpl_ids:
                v['locked'] = True
                if v.get('fixable'):
                    v['fixable'] = False
                    v['to_fix'] = False
                    v['note'] = _('Skipped - SKU is locked (unlock the product first to fix it)')
                    locked_count += 1

        if vals_list:
            Line.create([dict(wizard_id=self.id, **v) for v in vals_list])

        scope = self.company_id.name if self.company_id else _("all companies")
        if vals_list:
            self.message = _("Scan complete: %s issue(s) found in %s. Review below and click 'Apply Fixes'.") % (len(vals_list), scope)
        else:
            self.message = _("Scan complete: no SKU issues found in %s.") % scope
        self.state = 'preview'
        return self._reopen()

    # ------------------------------------------------------------------
    # APPLY
    # ------------------------------------------------------------------
    def action_apply(self):
        self.ensure_one()
        to_fix = self.line_ids.filtered(lambda l: l.to_fix and l.fixable)
        if not to_fix:
            raise UserError(_("No fixable findings are selected."))

        fixed = 0
        skipped_locked = 0
        for line in to_fix:
            variant = self.env['product.product'].browse(line.variant_id.id)
            if not variant.exists():
                continue
            # Never touch a locked product - it was deliberately frozen.
            if variant.product_tmpl_id.sku_locked:
                line.write({'note': _('Skipped - SKU is locked'), 'fixable': False, 'to_fix': False})
                skipped_locked += 1
                continue
            old_code = variant.default_code or ''

            # Mismatch with 'align' -> take the template code.
            # Duplicate / missing / regenerate -> pull a fresh code from the sequence.
            if line.issue_type == 'mismatch' and self.fix_method == 'align':
                new_code = line.template_code
            else:
                new_code = variant.product_tmpl_id._generate_default_code() \
                    if hasattr(variant.product_tmpl_id, '_generate_default_code') else False
                if not new_code:
                    line.note = _('Could not generate a code (category has no short code / sequence?)')
                    continue

            if not new_code or new_code == old_code:
                continue

            # Apply the code change, bypassing the SKU lock/validation guards
            variant.with_context(skip_sku_validation=True, skip_variant_sku_generation=True).write({
                'default_code': new_code,
            })

            # Recycle the freed code.
            # NOTE: for a 'duplicate' fix the old code is NOT freed (the keeper still
            # uses it), so it must not be recycled. Only mismatch/missing free a code.
            if self.recycle_freed and old_code and old_code != new_code \
                    and line.issue_type != 'duplicate':
                try:
                    self.env['product.sku.recycle.pool'].add_to_pool(
                        old_code, variant.product_tmpl_id.categ_id,
                        variant.company_id or self.env.company,
                        product_name=variant.name,
                    )
                except Exception as e:  # never let pool issues block the fix
                    _logger.warning("SKU Audit: could not recycle %s: %s", old_code, e)

            # Traceability note on the chatter
            if self.post_chatter:
                reason_map = {
                    'mismatch': _('Variant code aligned to product template (single-variant item)'),
                    'duplicate': _('Duplicate Internal Reference - reassigned a fresh code from the category sequence'),
                    'missing': _('Missing Internal Reference - generated from the category sequence'),
                }
                reason = reason_map.get(line.issue_type,
                                        dict(self._fields['fix_method'].selection).get(self.fix_method))
                body = Markup(
                    "<b>SKU Audit correction</b><br/>"
                    "Internal Reference changed: <b>%(old)s</b> &rarr; <b>%(new)s</b><br/>"
                    "Reason: %(reason)s<br/>"
                    "Previous reference kept here for traceability."
                ) % {
                    'old': old_code or '(none)',
                    'new': new_code,
                    'reason': reason,
                }
                variant.message_post(body=body)
                # also note on the template for visibility
                variant.product_tmpl_id.message_post(body=body)

            line.write({'proposed_code': new_code, 'done': True})
            fixed += 1

        self.state = 'done'
        msg = _("%s product(s) corrected.") % fixed
        if skipped_locked:
            msg += _(" %s skipped (SKU locked).") % skipped_locked
        self.message = msg
        return self._reopen()

    message = fields.Char(readonly=True)

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sku.audit.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class SkuAuditWizardLine(models.TransientModel):
    _name = 'sku.audit.wizard.line'
    _description = 'SKU Audit Finding'
    _order = 'issue_type, current_code'

    wizard_id = fields.Many2one('sku.audit.wizard', ondelete='cascade')
    issue_type = fields.Selection([
        ('mismatch', 'Template/Variant Mismatch'),
        ('duplicate', 'Duplicate Code'),
        ('missing', 'Missing Code'),
        ('variant_irregular', 'Multi-Variant Irregular'),
    ], string="Issue")
    template_id = fields.Many2one('product.template', string="Template")
    variant_id = fields.Many2one('product.product', string="Variant")
    product_name = fields.Char(string="Product")
    company_name = fields.Char(string="Company")
    current_code = fields.Char(string="Current Code")
    template_code = fields.Char(string="Template Code")
    proposed_code = fields.Char(string="Proposed Code")
    fixable = fields.Boolean(string="Fixable", default=True)
    locked = fields.Boolean(string="SKU Locked", default=False)
    to_fix = fields.Boolean(string="Fix?", default=True)
    done = fields.Boolean(string="Done", default=False)
    note = fields.Char(string="Note")
