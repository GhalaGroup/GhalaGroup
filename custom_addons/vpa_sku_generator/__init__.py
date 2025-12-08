# -*- coding: utf-8 -*-
# Part of Product Sequence Configuration. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2025 VPA Software Limited

from . import controllers
from . import models
from . import wizard


def _cleanup_old_views(env):
    """Clean up old view records that may have incorrect arch or orphaned views"""
    # Clear arch_db cache for our SKU form view
    env.cr.execute("""
        UPDATE ir_ui_view
        SET arch_db = NULL
        WHERE model = 'product.category'
        AND name = 'product.category.form.inherit.sku'
    """)
    # Delete orphaned views with old xpath (adds fields after name instead of notebook)
    # These are from older versions of the module
    env.cr.execute("""
        DELETE FROM ir_ui_view
        WHERE model = 'product.category'
        AND name = 'product.category.form.inherit'
        AND arch_db::text LIKE '%short_name%'
        AND arch_db::text LIKE '%position="after"%'
    """)


def pre_init_hook(env):
    """Pre-init hook to clean up old views before upgrade"""
    _cleanup_old_views(env)