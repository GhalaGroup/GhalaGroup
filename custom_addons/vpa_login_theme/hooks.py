# -*- coding: utf-8 -*-
# Part of VPA Login Theme. See LICENSE file for full copyright and licensing details.

def post_init_hook(env):
    """
    Post-installation hook to ensure menus are visible.
    This runs AFTER module installation to force correct menu configuration.
    """
    # Force set menu visibility to base.group_system (Administrator)
    system_group = env.ref('base.group_system')

    # VPA Applications menu
    vpa_menu = env.ref('vpa_login_theme.menu_vpa_applications', raise_if_not_found=False)
    if vpa_menu:
        vpa_menu.write({
            'group_ids': [(6, 0, [system_group.id])],
            'active': True,
        })
        print(f"✓ VPA Applications menu configured - Groups: {vpa_menu.group_ids.mapped('name')}")

    # Login Theme menu
    theme_menu = env.ref('vpa_login_theme.menu_vpa_login_theme', raise_if_not_found=False)
    if theme_menu:
        theme_menu.write({
            'group_ids': [(6, 0, [system_group.id])],
            'active': True,
        })
        print(f"✓ Login Theme menu configured - Groups: {theme_menu.group_ids.mapped('name')}")

    env.cr.commit()
    print("✓ VPA Login Theme menus configured successfully!")
