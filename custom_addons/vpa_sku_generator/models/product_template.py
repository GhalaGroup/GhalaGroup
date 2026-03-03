# -*- coding: utf-8 -*-
# Part of Product Sequence Configuration. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2025 VPA Software Limited

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    default_code = fields.Char(copy=False, readonly=False)

    sku_locked = fields.Boolean(
        string='Lock SKU',
        default=False,
        help='Prevent automatic SKU regeneration for this product and all its variants'
    )

    @api.constrains('categ_id')
    def _check_category_required(self):
        """Enforce category requirement if enabled in settings"""
        require_category = self.env['ir.config_parameter'].sudo().get_param(
            'vpa_sku_generator.require_category', 'True'
        ) == 'True'

        if require_category:
            for record in self:
                if not record.categ_id:
                    raise ValidationError(_('Product category is required. Please select a category.'))

    @api.constrains('default_code')
    def _check_sku_required(self):
        """Enforce SKU requirement if enabled in settings

        NOTE: This constraint is defined on product.template but SKU requirement
        should only be enforced on product.product (variants). Templates can have
        no SKU when using variants, as each variant has its own SKU.
        """
        # Templates don't need SKUs - only variants do
        # The constraint on variants is defined in product.product model
        return

    @api.onchange('default_code')
    def _onchange_default_code(self):
        """Block manual SKU entry if enabled in settings"""
        block_manual = self.env['ir.config_parameter'].sudo().get_param(
            'vpa_sku_generator.block_manual', 'False'
        ) == 'True'

        if block_manual and self.default_code and not self.env.context.get('skip_sku_validation'):
            # Check if the change is manual (not from auto-generation)
            if self._origin and self._origin.default_code != self.default_code:
                self.default_code = self._origin.default_code
                return {
                    'warning': {
                        'title': _('Manual SKU Entry Blocked'),
                        'message': _('Manual SKU entry is disabled. Use category selection to auto-generate SKU.')
                    }
                }

    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        """Show SKU preview when category changes (does NOT consume sequence)"""
        auto_generate = self.env['ir.config_parameter'].sudo().get_param(
            'vpa_sku_generator.auto_generate', 'True'
        ) == 'True'

        # Only show preview if enabled, product is not locked, and category is set
        if auto_generate and not self.sku_locked and self.categ_id:
            # Only update if no existing SKU or category changed
            if not self.default_code or (self._origin and self._origin.categ_id != self.categ_id):
                # Use preview method - reads sequence without consuming it
                # Actual sequence consumption happens in create() on save
                parent_categories = self.env['product.category'].search([
                    ('id', 'parent_of', self.categ_id.id)
                ], order="id asc")

                if all(cat.short_name for cat in parent_categories):
                    short_names = "/".join(parent_categories.mapped("short_name"))

                    # Check recycle pool first (preview only - don't consume)
                    enable_recycle = self.env['ir.config_parameter'].sudo().get_param(
                        'vpa_sku_generator.enable_recycle', 'True'
                    ) == 'True'
                    recycled_preview = False
                    if enable_recycle:
                        recycled = self.env['product.sku.recycle.pool'].search([
                            ('category_id', '=', self.categ_id.id),
                            ('company_id', '=', self.env.company.id)
                        ], order='sku_number asc', limit=1)
                        if recycled:
                            recycled_preview = recycled.name

                    if recycled_preview:
                        self.default_code = recycled_preview
                    else:
                        next_num = self.categ_id._get_next_sku_number_preview()
                        self.default_code = f"{short_names}/{str(next_num).zfill(5)}"

    def get_or_create_ir_sequence(self):
        """Get or create sequence for category, accounting for imported SKUs"""
        self.ensure_one()
        # Use the category's method to get the sequence code (includes full hierarchy path)
        sequence_code = self.categ_id._get_sequence_code()
        if not sequence_code:
            return False

        company_id = self.company_id.id or self.env.company.id

        # Check if sequence exists
        IrSequence = self.env["ir.sequence"].sudo().search([
            ("code", "=", sequence_code),
            ("company_id", "=", company_id)
        ])

        # Create if doesn't exist
        if not IrSequence:
            # Check for existing SKUs from imports to set correct starting number
            max_sku = self.categ_id._get_max_sku_number_from_products()
            next_number = max_sku + 1 if max_sku > 0 else 1

            # Build full category path for sequence name
            parent_categories = self.env['product.category'].search([
                ('id', 'parent_of', self.categ_id.id)
            ], order="id asc")
            full_path = "/".join(parent_categories.mapped("short_name"))

            IrSequence = self.env["ir.sequence"].sudo().create({
                "name": f"Product SKU Sequence: {full_path}",
                "code": sequence_code,
                "padding": 5,
                "number_next": next_number,
                "number_increment": 1,
                "company_id": company_id,
            })

        # Get next number using _next method
        return IrSequence._next()

    def _generate_default_code(self):
        """Generate SKU from category hierarchy or recycle pool"""
        self.ensure_one()

        if not self.categ_id:
            return False

        # Build category path
        parent_categories = self.env['product.category'].search([
            ('id', 'parent_of', self.categ_id.id)
        ], order="id asc")

        if not all(cat.short_name for cat in parent_categories):
            return False

        short_names = "/".join(parent_categories.mapped("short_name"))

        # Check if recycling is enabled
        enable_recycle = self.env['ir.config_parameter'].sudo().get_param(
            'vpa_sku_generator.enable_recycle', 'True'
        ) == 'True'

        if enable_recycle:
            # Try to get from recycle pool first
            recycled_sku = self.env['product.sku.recycle.pool'].get_from_pool(
                self.categ_id,
                self.company_id or self.env.company
            )
            if recycled_sku:
                return recycled_sku

        # Generate new sequence number
        sequence = self.get_or_create_ir_sequence()
        return f"{short_names}/{sequence}"

    def write(self, vals):
        """Override write to handle SKU generation and locking"""
        # Handle SKU locking
        for record in self:
            if record.sku_locked and 'default_code' in vals and vals['default_code'] != record.default_code:
                if not self.env.context.get('force_sku_update'):
                    raise UserError(_('SKU is locked for product "%s". Unlock it before making changes.') % record.name)

        result = super(ProductTemplate, self).write(vals)

        # Auto-generate SKU on category change
        if "categ_id" in vals:
            auto_generate = self.env['ir.config_parameter'].sudo().get_param(
                'vpa_sku_generator.auto_generate', 'True'
            ) == 'True'

            for record in self:
                if not record.sku_locked and auto_generate and not record.default_code:
                    default_code = record._generate_default_code()
                    if default_code:
                        super(ProductTemplate, record).with_context(skip_sku_validation=True).write({
                            'default_code': default_code
                        })

        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to auto-generate SKU"""
        auto_generate = self.env['ir.config_parameter'].sudo().get_param(
            'vpa_sku_generator.auto_generate', 'True'
        ) == 'True'

        res = super(ProductTemplate, self).create(vals_list)

        # Skip SKU generation if we're in a copy operation
        # The copy() method will handle SKU generation
        if self.env.context.get('skip_variant_sku_generation'):
            return res

        for record, vals in zip(res, vals_list):
            if auto_generate and "categ_id" in vals:
                # Always generate a real SKU on create() so the sequence is properly consumed.
                # The onchange only shows a preview (no sequence consumption), so we must
                # generate here. If the user provided a manual SKU (not from the onchange),
                # they would have set 'skip_sku_validation' context or block_manual would apply.
                # We skip generation only when a manual SKU was explicitly provided AND
                # it doesn't match the auto-generated pattern for this category.
                user_provided_sku = vals.get('default_code')
                categ = record.categ_id
                parent_categories = self.env['product.category'].search([
                    ('id', 'parent_of', categ.id)
                ], order="id asc") if categ else self.env['product.category']
                auto_prefix = "/".join(parent_categories.mapped("short_name")) + "/" if all(
                    cat.short_name for cat in parent_categories) else None

                # If user provided a SKU that doesn't match the auto-generated prefix, keep it
                if user_provided_sku and auto_prefix and not user_provided_sku.startswith(auto_prefix):
                    continue  # Preserve manually-entered SKU with different format

                # Generate the real SKU (consumes sequence exactly once on save)
                default_code = record._generate_default_code()
                if default_code:
                    record.with_context(skip_sku_validation=True).write({'default_code': default_code})

        return res

    def copy(self, default=None):
        """Override copy to generate new SKU for duplicated products"""
        default = default or {}
        # Remove lock on copy
        default['sku_locked'] = False

        # Use context to prevent variant from generating its own SKU during copy
        # The template copy will handle SKU generation for both template and variant
        template = super(ProductTemplate, self.with_context(skip_variant_sku_generation=True)).copy(default)

        # Always generate new SKU for duplicated product
        default_code = template._generate_default_code()
        if default_code:
            template.with_context(skip_sku_validation=True).write({'default_code': default_code})
            # Also update variant SKU(s)
            variants = template.product_variant_ids
            if len(variants) == 1:
                # Single variant: use same SKU as template
                variants.with_context(skip_sku_validation=True).write({'default_code': default_code})
            elif len(variants) > 1:
                # Multiple variants: add suffix
                sorted_variants = variants.sorted(
                    lambda v: (','.join(sorted(v.product_template_attribute_value_ids.mapped('name'))), v.id)
                )
                for idx, variant in enumerate(sorted_variants, 1):
                    variant.with_context(skip_sku_validation=True).write({
                        'default_code': f"{default_code}-{str(idx).zfill(3)}"
                    })

        return template

    def unlink(self):
        """Add SKU to recycle pool when product is deleted"""
        enable_recycle = self.env['ir.config_parameter'].sudo().get_param(
            'vpa_sku_generator.enable_recycle', 'True'
        ) == 'True'

        if enable_recycle:
            RecyclePool = self.env['product.sku.recycle.pool']
            for record in self:
                # Only recycle if SKU exists and is not locked
                if record.default_code and not record.sku_locked and record.categ_id:
                    # Don't recycle variant SKUs (those with -)
                    if '-' not in record.default_code:
                        RecyclePool.add_to_pool(
                            sku=record.default_code,
                            category=record.categ_id,
                            company=record.company_id or self.env.company,
                            product_name=record.name
                        )

        return super(ProductTemplate, self).unlink()

    def action_regenerate_sku(self):
        """Open regenerate SKU wizard for this product"""
        return {
            'name': _('Regenerate SKU'),
            'type': 'ir.actions.act_window',
            'res_model': 'regenerate.sku.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_product_ids': self.ids},
        }
