# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """v2.0.4: the yearly rate is now an explicit per-year value.

    Years created before this stored 0 meaning "use the scheme default";
    backfill them with that default so the displayed rate is real.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    years = env['vpa.commission.scheme.year'].search([('production_rate', '=', 0)])
    count = 0
    for year in years:
        default = year.scheme_id.production_rate
        if default:
            year.production_rate = default
            count += 1
    _logger.info('Commission migration: backfilled rate on %d year line(s).', count)
