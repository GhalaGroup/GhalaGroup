# -*- coding: utf-8 -*-
# Part of VPA Tanzania Localization. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2025 VPA Software Limited

from . import models


def _cleanup_duplicate_vrn_view(env):
    """Remove orphaned VRN view from old partner_vat_number module.

    This view (base_view_partner_form_inherit) adds a duplicate VRN field
    to the partner form. The Tanzania localization already adds VRN properly.
    """
    env.execute("""
        DELETE FROM ir_ui_view
        WHERE name = 'base_view_partner_form_inherit'
        AND model = 'res.partner'
        AND arch_db::text LIKE '%vrn%'
    """)


def _fix_vrn_format(env):
    """Fix VRN values that are missing dashes.

    Correct format: NN-NNNNNN-N (e.g., 40-123456-X)
    Incorrect format: NNNNNNNNN (e.g., 40123456X)

    This fixes VRN values entered without dashes to match Tanzania TRA format.
    """
    env.execute("""
        UPDATE res_partner
        SET vrn = CONCAT(SUBSTRING(vrn, 1, 2), '-', SUBSTRING(vrn, 3, 6), '-', SUBSTRING(vrn, 9, 1))
        WHERE vrn IS NOT NULL
        AND vrn != ''
        AND vrn NOT LIKE '%-%'
        AND LENGTH(vrn) = 9
    """)


def pre_init_hook(env):
    """Pre-init hook to clean up data before module upgrade.

    Performs:
    1. Removes duplicate VRN view from old modules
    2. Fixes VRN format (adds dashes where missing)
    """
    _cleanup_duplicate_vrn_view(env)
    _fix_vrn_format(env)
