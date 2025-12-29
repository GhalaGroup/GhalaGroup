# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    """Called before module installation.

    Currently no pre-initialization needed.
    """
    _logger.info("VPA UoM: Pre-init hook called")


def post_init_hook(env):
    """Restore from auto backup after module reinstall.

    If there's an auto backup from a previous uninstall,
    automatically restore the conversions.
    """
    _logger.info("VPA UoM: Checking for auto backup to restore...")

    try:
        # Check if backup model exists (it should after install)
        if 'uom.conversion.backup' in env:
            Backup = env['uom.conversion.backup']
            restored = Backup.restore_from_latest_backup()

            if restored:
                _logger.info("VPA UoM: Successfully restored from auto backup")
            else:
                _logger.info("VPA UoM: No auto backup found to restore")

    except Exception as e:
        _logger.warning(f"VPA UoM: Could not restore from backup: {e}")
        # Don't raise - allow installation to proceed


def uninstall_hook(env):
    """Create automatic backup before module uninstall.

    This ensures that all UoM conversion data is preserved
    and can be restored if the module is reinstalled.
    """
    _logger.info("VPA UoM: Creating automatic backup before uninstall...")

    try:
        Backup = env['uom.conversion.backup']
        backup = Backup.export_all_conversions(backup_type='auto_uninstall')

        if backup:
            _logger.info(f"VPA UoM: Auto backup created successfully: {backup.name}")
            _logger.info(f"VPA UoM: {backup.conversion_count} conversions backed up")
        else:
            _logger.info("VPA UoM: No conversions to backup")

    except Exception as e:
        _logger.error(f"VPA UoM: Failed to create auto backup: {e}")
        # Don't raise - allow uninstall to proceed even if backup fails
