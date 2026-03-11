# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

import logging

_logger = logging.getLogger(__name__)


def migrate_guarantees_to_year_lines(env):
    """
    Migration stub — vpa.commission.guarantee model has been removed.
    This hook is kept to avoid errors on re-upgrade.
    """
    _logger.info('Commission migration hook: guarantee model removed, nothing to migrate.')
