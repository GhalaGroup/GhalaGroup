# -*- coding: utf-8 -*-
# Part of Product Sequence Configuration. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2025 VPA Software Limited

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ProductProduct(models.Model):
    _inherit = "product.product"

    default_code = fields.Char(copy=False)
    sku_locked = fields.Boolean(related='product_tmpl_id.sku_locked', string='SKU Locked', readonly=True, store=False)

    class Constraint(models.Constraint):
        _constraint_name = 'default_code_unique'
        _definition = 'UNIQUE(default_code)'
        _message = 'Internal Reference (SKU) must be unique!'

    @api.constrains('default_code')
    def _check_sku_required(self):
        """Enforce SKU requirement if enabled in settings (for variants only)"""
        # Skip validation if context flag is set
        if self.env.context.get('skip_sku_validation'):
            return

        require_sku = self.env['ir.config_parameter'].sudo().get_param(
            'vpa_sku_generator.require_sku', 'True'
        ) == 'True'

        if require_sku:
            for record in self:
                if not record.default_code:
                    raise ValidationError(_('Internal Reference (SKU) is required. Please generate or enter an SKU.'))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate variant SKUs with sequential suffixes"""
        templates = self.env['product.template']
        for vals in vals_list:
            if 'product_tmpl_id' in vals:
                templates |= self.env['product.template'].browse(vals['product_tmpl_id'])

        res = super(ProductProduct, self).create(vals_list)

        # Generate SKUs for variants
        for variant, vals in zip(res, vals_list):
            # Skip if SKU manually provided or template is locked
            if 'default_code' in vals or variant.product_tmpl_id.sku_locked:
                continue

            # Generate variant SKU
            variant_sku = variant._generate_variant_sku()
            if variant_sku:
                super(ProductProduct, variant).with_context(skip_sku_validation=True).write({'default_code': variant_sku})

        return res

    def _generate_variant_sku(self):
        """Generate SKU for variant with sequential suffix

        Template must have base SKU already set (e.g., UDI/OFF/00001)
        Variants inherit template SKU:
        - Single variant: same as template (UDI/OFF/00001)
        - Multiple variants: template SKU + suffix (UDI/OFF/00001-001, -002, etc.)
        """
        self.ensure_one()

        template = self.product_tmpl_id

        # Template MUST have SKU already - don't generate here
        if not template.default_code or template.default_code == 'False':
            return False

        base_sku = template.default_code

        # If this is the only variant, use template SKU without suffix
        if len(template.product_variant_ids) == 1:
            return base_sku

        # For multiple variants, add sequential suffix based on variant attribute combination
        # Sort all variants by their attribute values for consistent ordering
        all_variants = template.product_variant_ids.sorted(
            lambda v: (
                ','.join(sorted(v.product_template_attribute_value_ids.mapped('name'))),
                v.id  # Fallback to ID for stability
            )
        )

        # Find the position of this variant (1-indexed)
        variant_index = 0
        for idx, variant in enumerate(all_variants, 1):
            if variant.id == self.id:
                variant_index = idx
                break

        if variant_index == 0:
            variant_index = len(all_variants)

        # Generate SKU with suffix
        return f"{base_sku}-{str(variant_index).zfill(3)}"

    def write(self, vals):
        """Prevent SKU changes if template is locked"""
        for record in self:
            if record.product_tmpl_id.sku_locked and 'default_code' in vals:
                if vals['default_code'] != record.default_code:
                    if not self.env.context.get('force_sku_update'):
                        raise UserError(
                            _('SKU is locked for product "%s". Unlock the product template before making changes.')
                            % record.display_name
                        )

        return super(ProductProduct, self).write(vals)

    def copy(self, default=None):
        """Generate new variant SKU when duplicating"""
        default = default or {}

        variant = super(ProductProduct, self).copy(default)

        # Generate new SKU for duplicated variant
        if not variant.product_tmpl_id.sku_locked:
            variant_sku = variant._generate_variant_sku()
            if variant_sku:
                super(ProductProduct, variant).with_context(skip_sku_validation=True).write({'default_code': variant_sku})

        return variant

    def unlink(self):
        """Variant SKUs are NOT recycled when deleted"""
        # Note: We don't add variant SKUs to recycle pool
        # Only template SKUs (without suffix) are recycled
        return super(ProductProduct, self).unlink()

    def action_regenerate_sku(self):
        """Regenerate SKU for this variant"""
        self.ensure_one()
        if self.product_tmpl_id.sku_locked:
            raise UserError(_('SKU is locked for this product. Unlock it before regenerating.'))

        new_sku = self._generate_variant_sku()
        if new_sku:
            super(ProductProduct, self).with_context(skip_sku_validation=True).write({'default_code': new_sku})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('SKU regenerated: %s') % new_sku,
                    'type': 'success',
                    'sticky': False,
                }
            }

    def action_toggle_sku_lock(self):
        """Toggle SKU lock for the product template"""
        self.ensure_one()
        self.product_tmpl_id.sku_locked = not self.product_tmpl_id.sku_locked

        status = 'locked' if self.product_tmpl_id.sku_locked else 'unlocked'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('SKU %s') % status.capitalize(),
                'message': _('SKU is now %s for "%s" and all its variants') % (status, self.product_tmpl_id.name),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_bulk_regenerate_sku(self):
        """Bulk regenerate SKUs for selected products

        Process:
        1. Group variants by template
        2. For each template, generate base SKU and assign to ALL variants with suffixes
        3. This ensures all variants of same template share the same base number
        """
        locked_products = self.filtered(lambda p: p.product_tmpl_id.sku_locked)
        if locked_products:
            raise UserError(
                _('Cannot regenerate SKUs for locked products:\n%s\n\nUnlock them first.') %
                '\n'.join(locked_products.mapped('display_name'))
            )

        regenerated = []
        skipped = []
        duplicates = []

        # Group products by template
        templates = self.mapped('product_tmpl_id')

        for template in templates:
            # If template has an existing SKU, add it to recycle pool before generating new one
            old_template_sku = template.default_code
            if old_template_sku and old_template_sku != 'False':
                # Add old SKU to recycle pool
                self.env['product.sku.recycle.pool'].add_to_pool(
                    old_template_sku,
                    template.categ_id,
                    template.company_id or self.env.company,
                    template.name
                )

            # Generate NEW SKU (will try recycle pool first, then sequence)
            base_sku = template._generate_default_code()
            if not base_sku:
                for variant in template.product_variant_ids:
                    skipped.append(f"{variant.display_name}: No category or category missing short codes")
                continue

            # Save template SKU
            template.with_context(skip_sku_validation=True).write({'default_code': base_sku})

            # Get ALL variants of this template (not just selected ones)
            all_variants = template.product_variant_ids.sorted(
                lambda v: (','.join(sorted(v.product_template_attribute_value_ids.mapped('name'))), v.id)
            )

            # If single variant, use base SKU without suffix
            if len(all_variants) == 1:
                variant = all_variants[0]
                old_sku = variant.default_code
                variant.with_context(skip_sku_validation=True).write({'default_code': base_sku})
                if variant in self:  # Only track if it was selected
                    regenerated.append(f"{variant.display_name}: {old_sku} → {base_sku}")
            else:
                # Multiple variants: assign base SKU + suffix
                for idx, variant in enumerate(all_variants, 1):
                    old_sku = variant.default_code
                    new_sku = f"{base_sku}-{str(idx).zfill(3)}"

                    # Check for duplicates
                    existing = self.env['product.product'].search([
                        ('default_code', '=', new_sku),
                        ('id', '!=', variant.id)
                    ], limit=1)

                    if existing:
                        if variant in self:
                            duplicates.append(f"{variant.display_name}: {new_sku} (already used)")
                    else:
                        variant.with_context(skip_sku_validation=True).write({'default_code': new_sku})
                        if variant in self:  # Only track if it was selected
                            regenerated.append(f"{variant.display_name}: {old_sku} → {new_sku}")

        # Build result message
        message_parts = []
        if regenerated:
            message_parts.append(f"✓ Regenerated {len(regenerated)} SKU(s):\n" + '\n'.join(regenerated[:5]))
            if len(regenerated) > 5:
                message_parts[-1] += f"\n... and {len(regenerated) - 5} more"

        if skipped:
            message_parts.append(f"⚠ Skipped {len(skipped)} product(s):\n" + '\n'.join(skipped[:5]))
            if len(skipped) > 5:
                message_parts[-1] += f"\n... and {len(skipped) - 5} more"

        if duplicates:
            message_parts.append(f"✗ Duplicate SKUs prevented {len(duplicates)} product(s):\n" + '\n'.join(duplicates[:5]))
            if len(duplicates) > 5:
                message_parts[-1] += f"\n... and {len(duplicates) - 5} more"

        # Show notification and reload
        message = '\n\n'.join(message_parts) if message_parts else 'No SKUs regenerated'

        # Return with notification and reload
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bulk Regenerate SKUs'),
                'message': message,
                'type': 'success' if regenerated and not duplicates else 'warning',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            }
        }
