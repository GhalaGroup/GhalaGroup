# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Migration script to clean up orphaned views from old 'effective_date_change' module.

    This fixes the duplicate "Change Effective Date" button issue caused by
    orphaned database records from the module before it was renamed to
    'vpa_effective_date_change'.
    """
    _logger.info("Running post-migration script for vpa_effective_date_change 19.0.1.2.1")

    # Find orphaned views from old module
    cr.execute("""
        SELECT imd.id, imd.module, imd.name, imd.model, imd.res_id
        FROM ir_model_data imd
        WHERE imd.module = 'effective_date_change'
          AND imd.model = 'ir.ui.view'
          AND imd.name IN ('effective_date_change', 'effective_date_change_privilege')
    """)

    orphaned_data = cr.fetchall()

    if orphaned_data:
        _logger.info(f"Found {len(orphaned_data)} orphaned view(s) from old 'effective_date_change' module")

        # Deactivate all orphaned views
        for data_id, module, name, model, res_id in orphaned_data:
            _logger.info(f"  Deactivating view: {module}.{name} (res_id={res_id})")
            cr.execute("""
                UPDATE ir_ui_view
                SET active = FALSE
                WHERE id = %s
            """, (res_id,))

        _logger.info("✓ Successfully deactivated orphaned views")
    else:
        _logger.info("No orphaned views found - database is clean")

    # Log completion
    _logger.info("Post-migration script completed successfully")
