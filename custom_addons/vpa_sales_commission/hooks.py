# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

import logging

_logger = logging.getLogger(__name__)


def migrate_guarantees_to_year_lines(env):
    """
    Post-migrate hook.

    - Legacy: vpa.commission.guarantee model removed (nothing to migrate).
    - v2.0.3: the rate is now an explicit per-year value (prefilled from the
      scheme default, freely editable per year). Years created earlier stored 0
      meaning "use the scheme default" — backfill those with the default so the
      displayed rate is real. Idempotent: only touches rows still at 0.
    """
    years = env['vpa.commission.scheme.year'].search([('production_rate', '=', 0)])
    count = 0
    for year in years:
        default = year.scheme_id.production_rate
        if default:
            year.production_rate = default
            count += 1
    if count:
        _logger.info('Commission migration: backfilled rate on %d year line(s) '
                     'from their scheme default.', count)
