# -*- coding: utf-8 -*-
from . import controllers
from . import models


def _post_init_hook(env):
    """
    Post-install/upgrade hook - runs on BOTH install AND upgrade in Odoo 14+
    1. Cleanup orphan report actions from Print menu (fixes duplicates)
    2. Restore from backup if available (preserves user configurations after reinstall)
    3. Create default footer configs for all companies that don't have them
    4. ALWAYS regenerate sale_production templates (fixes QWeb syntax errors)
    """
    import logging
    _logger = logging.getLogger(__name__)

    _logger.info("=" * 60)
    _logger.info("VPA Document Layout: POST_INIT_HOOK STARTING")
    _logger.info("=" * 60)

    # Step 1: Cleanup orphan VPA report actions to fix duplicate Print menu entries
    _logger.info("VPA Document Layout: Step 1 - Cleaning up orphan report actions...")
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
        else:
            _logger.info("VPA Document Layout: No orphan report actions found")
    except Exception as e:
        _logger.warning(f"VPA Document Layout: Could not cleanup orphan reports: {e}")

    # Step 2: Try to restore from any existing backup (only on fresh install)
    _logger.info("VPA Document Layout: Step 2 - Checking for backup to restore...")
    try:
        BackupModel = env['vpa.config.backup']
        restored = BackupModel.restore_from_latest_backup()
        if restored:
            _logger.info("VPA Document Layout: Restored from backup")
            env.cr.commit()  # Commit the restored data
        else:
            _logger.info("VPA Document Layout: No backup to restore")
    except Exception as e:
        _logger.warning(f"VPA Document Layout: Could not restore backup: {e}")

    # Step 3: Create default footers for companies that still don't have any
    _logger.info("VPA Document Layout: Step 3 - Initializing default footers...")
    try:
        env['vpa.footer.config'].init_default_footers_all_companies()
        _logger.info("VPA Document Layout: Default footers initialized")
    except Exception as e:
        _logger.warning(f"VPA Document Layout: Could not init footers: {e}")

    # Step 4: ALWAYS regenerate ALL sale_production templates to fix QWeb syntax
    # This MUST run on every install/upgrade to fix the broken format string syntax
    _logger.info("VPA Document Layout: Step 4 - REGENERATING ALL SALE_PRODUCTION TEMPLATES...")
    try:
        production_templates = env['vpa.document.template'].search([
            ('document_type', '=', 'sale_production')
        ])
        _logger.info(f"VPA Document Layout: Found {len(production_templates)} sale_production templates to regenerate")

        for template in production_templates:
            _logger.info(f"VPA Document Layout: Regenerating template: {template.name} (ID: {template.id})")
            # Delete existing QWeb views for this template
            existing_views = env['ir.ui.view'].search([
                '|', '|',
                ('key', 'like', f'%template_{template.id}%'),
                ('key', 'like', f'%inherit_{template.id}%'),
                ('name', 'like', f'%{template.id}')
            ])
            if existing_views:
                _logger.info(f"VPA Document Layout: Deleting {len(existing_views)} existing views")
                existing_views.unlink()
            # Recreate the QWeb template with FIXED syntax
            template._create_qweb_template()
            _logger.info(f"VPA Document Layout: Template {template.id} regenerated successfully")

        _logger.info(f"VPA Document Layout: Successfully regenerated {len(production_templates)} templates")
    except Exception as e:
        _logger.error(f"VPA Document Layout: FAILED to regenerate templates: {e}")
        import traceback
        _logger.error(traceback.format_exc())

    _logger.info("=" * 60)
    _logger.info("VPA Document Layout: POST_INIT_HOOK COMPLETED")
    _logger.info("=" * 60)


def _uninstall_hook(env):
    """
    Pre-uninstall hook: Auto-backup all VPA configurations before module is removed.
    This ensures user data is preserved and can be restored on reinstall.
    """
    BackupModel = env['vpa.config.backup']
    BackupModel.export_all_configs(backup_type='auto_uninstall')
    env.cr.commit()  # Ensure backup is saved before uninstall continues
