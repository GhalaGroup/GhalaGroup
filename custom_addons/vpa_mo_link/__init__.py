# -*- coding: utf-8 -*-
from . import models
from . import wizard


def post_init_hook(env):
    """
    Post-installation hook to create Production route rules for all warehouses.
    This ensures the Production route is functional immediately after module installation.
    """
    env['stock.warehouse']._create_production_route_rules()
