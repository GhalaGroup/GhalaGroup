# -*- coding: utf-8 -*-
# Part of VPA Tanzania Localization. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2025 VPA Software Limited

import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Override vat field label for Tanzania (applies to both companies and individuals)
    vat = fields.Char(
        string='TIN',
        tracking=True,  # Enable audit trail
    )

    # Add VRN field for VAT Registration Number
    vrn = fields.Char(
        string='VRN',
        copy=False,  # Don't copy VRN when duplicating partner
        tracking=True,  # Enable audit trail
    )

    # Override zip field label for Tanzania (P.O. Box instead of Zip)
    zip = fields.Char(
        string='P.O. Box',
        tracking=True,
    )

    # Note: Ward and Region fields are defined in res_country_ward.py to avoid duplication
    # Note: SQL constraints for vat and vrn uniqueness are inherited from partner_vat_number
    # or will be created automatically by Odoo from existing database constraints

    @api.constrains('vat')
    def _check_tin_format(self):
        """Validate TIN format for Tanzanian partners."""
        for partner in self:
            if partner.vat and partner.country_id and partner.country_id.code == 'TZ':
                # Remove common separators
                tin_clean = partner.vat.replace('-', '').replace(' ', '').replace('.', '')

                # TIN should be 9 digits
                if not re.match(r'^\d{9}$', tin_clean):
                    raise ValidationError(_(
                        'Invalid TIN format for Tanzania!\n\n'
                        'TIN must be 9 digits.\n'
                        'Example: 123-456-789 or 123456789\n\n'
                        'Your input: %s'
                    ) % partner.vat)

    @api.constrains('vrn')
    def _check_vrn_format(self):
        """Validate VRN format for Tanzanian partners."""
        for partner in self:
            if partner.vrn and partner.country_id and partner.country_id.code == 'TZ':
                # Remove common separators
                vrn_clean = partner.vrn.replace('-', '').replace(' ', '').replace('.', '')

                # VRN should be 10 characters starting with 40, 41, or 42
                if not re.match(r'^4[012]\d{7}[A-Z0-9]$', vrn_clean):
                    raise ValidationError(_(
                        'Invalid VRN format for Tanzania!\n\n'
                        'VRN must:\n'
                        '- Start with "40", "41", or "42" (Tanzania VAT prefix)\n'
                        '- Followed by 7 digits\n'
                        '- End with 1 alphanumeric check character\n'
                        'Example: 40-1234567-X or 411234567X\n\n'
                        'Your input: %s'
                    ) % partner.vrn)

    @api.model
    def create(self, vals):
        """Normalize TIN and VRN on create."""
        if 'vat' in vals and vals.get('vat'):
            vals['vat'] = self._normalize_tax_number(vals['vat'])
        if 'vrn' in vals and vals.get('vrn'):
            vals['vrn'] = self._normalize_tax_number(vals['vrn'])
        return super(ResPartner, self).create(vals)

    def write(self, vals):
        """Normalize TIN and VRN on write."""
        if 'vat' in vals and vals.get('vat'):
            vals['vat'] = self._normalize_tax_number(vals['vat'])
        if 'vrn' in vals and vals.get('vrn'):
            vals['vrn'] = self._normalize_tax_number(vals['vrn'])
        return super(ResPartner, self).write(vals)

    def _normalize_tax_number(self, tax_number):
        """Remove extra spaces and normalize format."""
        if not tax_number:
            return tax_number
        # Remove multiple spaces, leading/trailing spaces
        return ' '.join(tax_number.split()).upper()
