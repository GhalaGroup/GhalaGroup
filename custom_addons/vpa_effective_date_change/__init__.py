from . import models
from . import wizard


def pre_init_check(cr):
    from odoo.service import common
    from odoo.exceptions import UserError
    version_info = common.exp_version()
    server_serie = version_info.get('server_serie')
    if server_serie not in ['16.0', '19.0']:
        raise UserError(('This module supports Odoo Version 16.0 and 19.0 only, found ' + server_serie))
    return True
