# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from . import models
from . import wizard


def pre_init_check(cr):
    """Pre-initialization check to ensure Odoo version compatibility."""
    from odoo.service import common
    from odoo.exceptions import UserError
    version_info = common.exp_version()
    server_serie = version_info.get('server_serie')
    if server_serie != '19.0':
        raise UserError('This module supports Odoo Version 19.0 only, found ' + server_serie)
    return True
