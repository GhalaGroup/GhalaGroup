# -*- coding: utf-8 -*-
# Part of Product Sequence Configuration. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2025 VPA Software Limited

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RegenerateSkuWizard(models.TransientModel):
    _name = 'regenerate.sku.wizard'
    _description = 'Regenerate Product SKUs Wizard'

    scope = fields.Selection([
        ('all', 'All Products'),
        ('category', 'By Category'),
        ('selection', 'Selected Products'),
    ], string='Regenerate Scope', default='all', required=True)

    category_id = fields.Many2one(
        'product.category',
        string='Category',
        help='Only regenerate SKUs for products in this category'
    )

    product_ids = fields.Many2many(
        'product.template',
        string='Products',
        help='Specific products to regenerate'
    )

    respect_locks = fields.Boolean(
        string='Respect SKU Locks',
        default=True,
        help='Skip products with locked SKUs'
    )

    use_recycle_pool = fields.Boolean(
        string='Use Recycled SKUs',
        default=True,
        help='Reuse deleted SKUs from recycle pool before generating new ones'
    )

    reset_sequence = fields.Boolean(
        string='Reset Sequence',
        default=False,
        help='Reset category sequence and reassign all products starting from 00001. Maintains recycle pool for gaps.'
    )

    preview_line_ids = fields.One2many(
        'regenerate.sku.wizard.line',
        'wizard_id',
        string='Preview'
    )

    total_products = fields.Integer(
        string='Total Products',
        compute='_compute_statistics'
    )

    locked_products = fields.Integer(
        string='Locked Products',
        compute='_compute_statistics'
    )

    products_to_update = fields.Integer(
        string='Products to Update',
        compute='_compute_statistics'
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('preview', 'Preview'),
        ('done', 'Done'),
    ], default='draft', required=True)

    @api.depends('preview_line_ids', 'preview_line_ids.will_update')
    def _compute_statistics(self):
        for wizard in self:
            wizard.total_products = len(wizard.preview_line_ids)
            wizard.locked_products = len(wizard.preview_line_ids.filtered(lambda l: l.is_locked))
            wizard.products_to_update = len(wizard.preview_line_ids.filtered(lambda l: l.will_update))

    @api.onchange('scope', 'category_id')
    def _onchange_scope(self):
        """Update product_ids based on scope selection"""
        if self.scope == 'category' and not self.category_id:
            self.product_ids = False
        elif self.scope != 'selection':
            self.product_ids = False

    def action_generate_preview(self):
        """Generate preview of SKU changes"""
        self.ensure_one()

        # Clear existing preview
        self.preview_line_ids.unlink()

        # Get products based on scope (these are templates)
        templates = self._get_products_to_process()

        if not templates:
            raise UserError(_('No products found for the selected scope.'))

        # If reset_sequence, we need to simulate sequential SKU assignment
        if self.reset_sequence:
            preview_lines = self._generate_reset_sequence_preview(templates)
        else:
            # Normal preview - just show format
            preview_lines = []
            for template in templates:
                # For templates with variants, show each variant
                for variant in template.product_variant_ids:
                    is_locked = template.sku_locked
                    will_skip = is_locked and self.respect_locks

                    # Generate new SKU (simulation)
                    if not will_skip:
                        new_sku = self._simulate_new_sku(template)
                    else:
                        new_sku = variant.default_code

                    preview_lines.append((0, 0, {
                        'product_tmpl_id': template.id,
                        'product_variant_id': variant.id,
                        'current_sku': variant.default_code or '',
                        'new_sku': new_sku or '',
                        'is_locked': is_locked,
                        'will_update': not will_skip and (variant.default_code != new_sku),
                    }))

        self.preview_line_ids = preview_lines
        self.state = 'preview'

        return {
            'name': _('Regenerate SKUs - Preview'),
            'type': 'ir.actions.act_window',
            'res_model': 'regenerate.sku.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_regenerate(self):
        """Execute SKU regeneration"""
        self.ensure_one()

        if self.state != 'preview':
            raise UserError(_('Please generate preview first.'))

        updated_count = 0

        # If reset_sequence is enabled, handle it specially
        if self.reset_sequence:
            updated_count = self._reset_sequence_for_category()
        else:
            lines_to_update = self.preview_line_ids.filtered(lambda l: l.will_update)

            if not lines_to_update:
                raise UserError(_('No products to update.'))
            # Normal regeneration
            for line in lines_to_update:
                product = line.product_id

                # Generate new SKU
                new_sku = product.with_context(
                    force_sku_update=True,
                    skip_sku_validation=True
                )._generate_default_code()

                if new_sku:
                    product.with_context(
                        force_sku_update=True,
                        skip_sku_validation=True
                    ).write({'default_code': new_sku})
                    updated_count += 1

        self.state = 'done'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%d product SKUs regenerated successfully.') % updated_count,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_regenerate_and_lock(self):
        """Regenerate SKUs and lock all products"""
        self.ensure_one()

        # First regenerate
        result = self.action_regenerate()

        # Then lock all templates
        if self.reset_sequence:
            templates = self._get_products_to_process()
        else:
            lines_to_update = self.preview_line_ids.filtered(lambda l: l.will_update)
            templates = lines_to_update.mapped('product_tmpl_id')

        # Lock all templates
        templates.with_context(skip_sku_validation=True).write({'sku_locked': True})

        # Update message
        if result.get('type') == 'ir.actions.client':
            if result['params'].get('message'):
                result['params']['message'] += '\n\n🔒 All product SKUs have been locked.'

        return result

    def action_back_to_draft(self):
        """Go back to draft state"""
        self.preview_line_ids.unlink()
        self.state = 'draft'
        return {
            'name': _('Regenerate SKUs'),
            'type': 'ir.actions.act_window',
            'res_model': 'regenerate.sku.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _get_products_to_process(self):
        """Get products based on scope"""
        if self.scope == 'selection':
            return self.product_ids
        elif self.scope == 'category':
            if not self.category_id:
                raise UserError(_('Please select a category.'))
            return self.env['product.template'].search([
                ('categ_id', '=', self.category_id.id)
            ])
        else:  # all
            return self.env['product.template'].search([])

    def _simulate_new_sku(self, product):
        """Simulate what the new SKU would be"""
        if not product.categ_id:
            return False

        # Build category path
        parent_categories = self.env['product.category'].search([
            ('id', 'parent_of', product.categ_id.id)
        ], order="id asc")

        if not all(cat.short_name for cat in parent_categories):
            return False

        short_names = "/".join(parent_categories.mapped("short_name"))

        # For preview, just show format (don't actually consume sequences)
        return f"{short_names}/XXXXX"

    def _generate_reset_sequence_preview(self, templates):
        """Generate preview with actual SKU numbers when reset_sequence is enabled"""
        preview_lines = []

        # Build category path
        if not templates:
            return preview_lines

        first_template = templates[0]
        parent_categories = self.env['product.category'].search([
            ('id', 'parent_of', first_template.categ_id.id)
        ], order="id asc")

        if not all(cat.short_name for cat in parent_categories):
            return preview_lines

        short_names = "/".join(parent_categories.mapped("short_name"))

        # Simulate sequential assignment starting from 00001
        sku_counter = 1

        for template in templates:
            is_locked = template.sku_locked
            will_skip = is_locked and self.respect_locks

            if will_skip:
                # Skip locked products
                for variant in template.product_variant_ids:
                    preview_lines.append((0, 0, {
                        'product_tmpl_id': template.id,
                        'product_variant_id': variant.id,
                        'current_sku': variant.default_code or '',
                        'new_sku': variant.default_code or '',
                        'is_locked': is_locked,
                        'will_update': False,
                    }))
            else:
                # Assign new SKU
                base_sku = f"{short_names}/{str(sku_counter).zfill(5)}"

                # Get all variants
                all_variants = template.product_variant_ids.sorted(
                    lambda v: (','.join(sorted(v.product_template_attribute_value_ids.mapped('name'))), v.id)
                )

                if len(all_variants) == 1:
                    # Single variant - no suffix
                    variant = all_variants[0]
                    preview_lines.append((0, 0, {
                        'product_tmpl_id': template.id,
                        'product_variant_id': variant.id,
                        'current_sku': variant.default_code or '',
                        'new_sku': base_sku,
                        'is_locked': is_locked,
                        'will_update': True,
                    }))
                else:
                    # Multiple variants - add suffix
                    for idx, variant in enumerate(all_variants, 1):
                        variant_sku = f"{base_sku}-{str(idx).zfill(3)}"
                        preview_lines.append((0, 0, {
                            'product_tmpl_id': template.id,
                            'product_variant_id': variant.id,
                            'current_sku': variant.default_code or '',
                            'new_sku': variant_sku,
                            'is_locked': is_locked,
                            'will_update': True,
                        }))

                sku_counter += 1

        return preview_lines

    def _reset_sequence_for_category(self):
        """Reset sequence and reassign all products in category starting from 00001

        Process:
        1. Delete all SKUs from recycle pool for this category
        2. Reset sequence to 1
        3. Reassign all products starting from 00001, 00002, 00003...
        """
        if not self.category_id:
            raise UserError(_('Reset Sequence requires selecting a category.'))

        # Get all templates in category (not variants)
        templates = self.env['product.template'].search([
            ('categ_id', '=', self.category_id.id)
        ], order='id asc')

        if self.respect_locks:
            templates = templates.filtered(lambda t: not t.sku_locked)

        if not templates:
            return 0

        # Build category path
        parent_categories = self.env['product.category'].search([
            ('id', 'parent_of', self.category_id.id)
        ], order="id asc")

        if not all(cat.short_name for cat in parent_categories):
            raise UserError(_('Category or parent categories missing short codes.'))

        short_names = "/".join(parent_categories.mapped("short_name"))

        # Step 1: Clear recycle pool for this category
        recycle_pool = self.env['product.sku.recycle.pool']
        pool_skus = recycle_pool.search([
            ('category_id', '=', self.category_id.id)
        ])
        pool_skus.unlink()

        # Step 2: Reset the sequence for this category to 1
        # Use the category's method to get the sequence code (includes full hierarchy path)
        sequence_code = self.category_id._get_sequence_code()
        company_id = templates[0].company_id.id or self.env.company.id
        sequence = self.env['ir.sequence'].sudo().search([
            ('code', '=', sequence_code),
            ('company_id', '=', company_id)
        ], limit=1) if sequence_code else False

        if sequence:
            sequence.sudo().write({'number_next': 1})

        # Step 3: Reassign all products from 00001, 00002, 00003...
        # Build SKUs manually to match preview exactly
        updated_count = 0
        sku_counter = 1

        for template in templates:
            # Build base SKU manually (matching preview logic)
            base_sku = f"{short_names}/{str(sku_counter).zfill(5)}"

            # Get all variants sorted the same way as preview
            all_variants = template.product_variant_ids.sorted(
                lambda v: (','.join(sorted(v.product_template_attribute_value_ids.mapped('name'))), v.id)
            )

            if len(all_variants) == 1:
                # Single variant - use base SKU without suffix
                variant = all_variants[0]
                variant.with_context(
                    force_sku_update=True,
                    skip_sku_validation=True
                ).write({'default_code': base_sku})
            else:
                # Multiple variants - add suffix -001, -002, -003...
                for idx, variant in enumerate(all_variants, 1):
                    variant_sku = f"{base_sku}-{str(idx).zfill(3)}"
                    variant.with_context(
                        force_sku_update=True,
                        skip_sku_validation=True
                    ).write({'default_code': variant_sku})

            # Also update template default_code to base SKU
            template.with_context(
                force_sku_update=True,
                skip_sku_validation=True
            ).write({'default_code': base_sku})

            updated_count += 1
            sku_counter += 1

        return updated_count


class RegenerateSkuWizardLine(models.TransientModel):
    _name = 'regenerate.sku.wizard.line'
    _description = 'Regenerate SKU Wizard Line'
    _order = 'product_tmpl_id, product_variant_id'

    wizard_id = fields.Many2one(
        'regenerate.sku.wizard',
        required=True,
        ondelete='cascade'
    )

    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product Template',
        required=True
    )

    product_variant_id = fields.Many2one(
        'product.product',
        string='Product Variant',
        required=True
    )

    product_name = fields.Char(
        string='Product Name',
        compute='_compute_product_display'
    )

    category_name = fields.Char(
        related='product_tmpl_id.categ_id.display_name',
        string='Category'
    )

    @api.depends('product_variant_id', 'product_tmpl_id')
    def _compute_product_display(self):
        for line in self:
            if line.product_variant_id:
                # Get variant attributes
                attributes = line.product_variant_id.product_template_attribute_value_ids
                if attributes:
                    attr_str = ', '.join(attributes.mapped('name'))
                    line.product_name = f"{line.product_tmpl_id.name} ({attr_str})"
                else:
                    line.product_name = line.product_tmpl_id.name
            else:
                line.product_name = line.product_tmpl_id.name if line.product_tmpl_id else ''

    current_sku = fields.Char(
        string='Current SKU'
    )

    new_sku = fields.Char(
        string='New SKU'
    )

    is_locked = fields.Boolean(
        string='Locked'
    )

    will_update = fields.Boolean(
        string='Will Update'
    )

    status = fields.Char(
        string='Status',
        compute='_compute_status'
    )

    @api.depends('is_locked', 'will_update', 'current_sku', 'new_sku')
    def _compute_status(self):
        for line in self:
            if line.is_locked:
                line.status = 'Locked - Skipped'
            elif line.will_update:
                line.status = 'Will Update'
            elif line.current_sku == line.new_sku:
                line.status = 'No Change'
            else:
                line.status = 'Skipped'
