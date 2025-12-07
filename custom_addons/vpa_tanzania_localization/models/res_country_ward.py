# -*- coding: utf-8 -*-
# Part of VPA Tanzania Localization. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2025 VPA Software Limited

from odoo import models, fields, api


class CountryWard(models.Model):
    _name = 'res.country.ward'
    _description = 'Country Ward (Tanzania Administrative Division)'
    _order = 'region_id, name'

    name = fields.Char(
        string='Ward Name',
        required=True,
        translate=True,
    )

    code = fields.Char(
        string='Ward Code',
        help='Ward code for identification',
    )

    country_id = fields.Many2one(
        'res.country',
        string='Country',
        required=True,
    )

    region_id = fields.Many2one(
        'res.country.region',
        string='Region',
        required=True,
        domain="[('country_id', '=', country_id)]",
    )

    class Constraint(models.Constraint):
        _constraint_name = 'name_code_uniq'
        _definition = 'unique(country_id, region_id, name)'
        _message = 'Ward name must be unique per region!'


class CountryRegion(models.Model):
    _name = 'res.country.region'
    _description = 'Country Region (Tanzania Main Administrative Division)'
    _order = 'name'

    name = fields.Char(
        string='Region Name',
        required=True,
        translate=True,
    )

    code = fields.Char(
        string='Region Code',
        help='Region code for identification',
    )

    country_id = fields.Many2one(
        'res.country',
        string='Country',
        required=True,
    )

    city_name = fields.Char(
        string='City Name',
        help='The city name to display for addresses in this region. If not set, uses region name.',
    )

    ward_ids = fields.One2many(
        'res.country.ward',
        'region_id',
        string='Wards',
    )

    class Constraint(models.Constraint):
        _constraint_name = 'name_code_uniq'
        _definition = 'unique(country_id, name)'
        _message = 'Region name must be unique per country!'


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Add region field
    region_id = fields.Many2one(
        'res.country.region',
        string='Region',
        domain="[('country_id', '=?', country_id)]",
        tracking=True,
    )

    # Update ward to link with region
    ward_id = fields.Many2one(
        'res.country.ward',
        string='Ward',
        domain="[('region_id', '=?', region_id), ('country_id', '=?', country_id)]",
        tracking=True,
    )

    # Update city to be related to ward/region but still allow manual entry
    city = fields.Char(
        string='City/District',
        tracking=True,
    )

    @api.onchange('region_id')
    def _onchange_region_id(self):
        """Clear ward when region changes."""
        if self.region_id:
            # Clear ward if it doesn't belong to new region
            if self.ward_id and self.ward_id.region_id != self.region_id:
                self.ward_id = False
            # Auto-suggest city from region's city_name or name
            if not self.city and self.region_id:
                self.city = self.region_id.city_name or self.region_id.name
        else:
            self.ward_id = False

    @api.onchange('ward_id')
    def _onchange_ward_id(self):
        """Update city suggestion when ward changes."""
        if self.ward_id:
            # Auto-set country from ward
            if self.ward_id.country_id != self.country_id:
                self.country_id = self.ward_id.country_id
            # Auto-set region from ward
            if self.ward_id.region_id != self.region_id:
                self.region_id = self.ward_id.region_id
            # Suggest city from ward's region (use city_name if available)
            if not self.city:
                self.city = self.ward_id.region_id.city_name or self.ward_id.region_id.name

    @api.onchange('country_id')
    def _onchange_country_id(self):
        """Clear Tanzania-specific fields when country changes."""
        res = super(ResPartner, self)._onchange_country_id()
        if self.country_id and self.country_id.code != 'TZ':
            self.region_id = False
            self.ward_id = False
        return res
