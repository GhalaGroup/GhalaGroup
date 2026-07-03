# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from . import models
from . import wizard


def _nns_post_init_enable(env):
    """On INSTALL ONLY, turn on negative-stock prevention for every existing
    company. New companies get it via the field default (True).

    Deliberately runs only at install (post_init_hook), NOT on upgrade: if a
    company later turns the feature OFF, upgrading the module must keep it off.
    Do NOT add a migration that re-enables it - that would override a company's
    deliberate choice.

    This does NOT touch the inventory-adjustment approval feature, which stays
    opt-in (default False)."""
    env['res.company'].sudo().search([]).write({'nns_enabled': True})
