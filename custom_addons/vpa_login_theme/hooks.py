# -*- coding: utf-8 -*-
# Part of VPA Login Theme. See LICENSE file for full copyright and licensing details.

import logging

_logger = logging.getLogger(__name__)

def _fix_menu_groups(env):
    """Helper function to fix menu groups"""
    try:
        system_group = env.ref('base.group_system')

        # VPA Applications menu
        vpa_menu = env.ref('vpa_login_theme.menu_vpa_applications', raise_if_not_found=False)
        if vpa_menu:
            vpa_menu.write({
                'group_ids': [(6, 0, [system_group.id])],
                'active': True,
            })
            _logger.info("✓ VPA Applications menu configured - Groups: %s", vpa_menu.group_ids.mapped('name'))

        # Login Theme menu
        theme_menu = env.ref('vpa_login_theme.menu_vpa_login_theme', raise_if_not_found=False)
        if theme_menu:
            theme_menu.write({
                'group_ids': [(6, 0, [system_group.id])],
                'active': True,
            })
            _logger.info("✓ Login Theme menu configured - Groups: %s", theme_menu.group_ids.mapped('name'))

        _logger.info("✓ VPA Login Theme menus configured successfully!")
    except Exception as e:
        _logger.error("Error configuring VPA Login Theme menus: %s", e)

def post_init_hook(env):
    """
    Post-installation hook - runs after module installation.
    """
    _logger.info("Running post_init_hook for VPA Login Theme...")
    _fix_menu_groups(env)

def post_load_hook():
    """
    Post-load hook - runs every time the module is loaded (including upgrades).
    This ensures menu visibility is always correct.
    """
    # Note: post_load doesn't receive env, we need to get it differently
    # This hook is called without env parameter, so we skip it
    # The post_init hook should be enough for fresh installs
    pass
