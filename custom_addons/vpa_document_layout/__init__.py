# -*- coding: utf-8 -*-
from . import controllers
from . import models


def _post_init_hook(env):
    """
    Post-install hook:
    1. Cleanup orphan report actions from Print menu (fixes duplicates)
    2. Restore from backup if available (preserves user configurations after reinstall)
    3. Create default footer configs for all companies that don't have them
    """
    import logging
    _logger = logging.getLogger(__name__)

    # Step 1: Cleanup orphan VPA report actions to fix duplicate Print menu entries
    _logger.info("VPA Document Layout: Cleaning up orphan report actions...")
    try:
        orphan_reports = env['ir.actions.report'].search([
            ('report_name', 'like', 'vpa_document_layout.report_template_%')
        ])
        template_report_ids = env['vpa.document.template'].search([]).mapped('report_action_id').ids

        orphan_count = 0
        for report in orphan_reports:
            if report.id not in template_report_ids:
                _logger.info(f"Deleting orphan report: {report.name} (ID: {report.id})")
                report.unlink()
                orphan_count += 1

        if orphan_count:
            _logger.info(f"VPA Document Layout: Removed {orphan_count} orphan report action(s)")
    except Exception as e:
        _logger.warning(f"VPA Document Layout: Could not cleanup orphan reports: {e}")

    # Step 2: Try to restore from any existing backup
    BackupModel = env['vpa.config.backup']
    restored = BackupModel.restore_from_latest_backup()

    if restored:
        env.cr.commit()  # Commit the restored data

    # Step 3: Create default footers for companies that still don't have any
    env['vpa.footer.config'].init_default_footers_all_companies()


def _uninstall_hook(env):
    """
    Pre-uninstall hook: Auto-backup all VPA configurations before module is removed.
    This ensures user data is preserved and can be restored on reinstall.
    """
    BackupModel = env['vpa.config.backup']
    BackupModel.export_all_configs(backup_type='auto_uninstall')
    env.cr.commit()  # Ensure backup is saved before uninstall continues
