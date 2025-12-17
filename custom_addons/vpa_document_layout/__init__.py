# -*- coding: utf-8 -*-
from . import controllers
from . import models


def _post_init_hook(env):
    """
    Post-install hook:
    1. Restore from backup if available (preserves user configurations after reinstall)
    2. Create default footer configs for all companies that don't have them
    """
    # First, try to restore from any existing backup
    BackupModel = env['vpa.config.backup']
    restored = BackupModel.restore_from_latest_backup()

    if restored:
        env.cr.commit()  # Commit the restored data

    # Then create default footers for companies that still don't have any
    env['vpa.footer.config'].init_default_footers_all_companies()


def _uninstall_hook(env):
    """
    Pre-uninstall hook: Auto-backup all VPA configurations before module is removed.
    This ensures user data is preserved and can be restored on reinstall.
    """
    BackupModel = env['vpa.config.backup']
    BackupModel.export_all_configs(backup_type='auto_uninstall')
    env.cr.commit()  # Ensure backup is saved before uninstall continues
