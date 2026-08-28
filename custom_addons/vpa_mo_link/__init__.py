# -*- coding: utf-8 -*-
from . import models
from . import wizard


def post_init_hook(env):
    """
    Post-installation hook to create Production route rules for all warehouses.
    This ensures the Production route is functional immediately after module installation.
    """
    env['stock.warehouse']._create_production_route_rules()


def uninstall_hook(env):
    """
    Detach the Manufacturing Home router from the Manufacturing root menu.

    The menu record belongs to mrp, so uninstalling this module would otherwise
    leave it pointing at a deleted server action, breaking the app entirely.
    """
    menu = env.ref('mrp.menu_mrp_root', raise_if_not_found=False)
    if menu and menu.action and menu.action._name == 'ir.actions.server':
        menu.action = False
