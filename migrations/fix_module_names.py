#!/usr/bin/env python3
"""
Migration script to fix module names in Odoo.sh database
Run this via Odoo.sh shell or add to pre-install hook
"""

def migrate(cr, version):
    """Fix module names in database"""

    # Fix 1: Rename partner-vat-number to partner_vat_number
    cr.execute("""
        UPDATE ir_module_module
        SET name = 'partner_vat_number'
        WHERE name = 'partner-vat-number'
    """)

    cr.execute("""
        UPDATE ir_model_data
        SET module = 'partner_vat_number'
        WHERE module = 'partner-vat-number'
    """)

    # Fix 2: Rename product_sequence to vpa_sku_generator
    cr.execute("""
        UPDATE ir_module_module
        SET name = 'vpa_sku_generator'
        WHERE name = 'product_sequence'
    """)

    cr.execute("""
        UPDATE ir_model_data
        SET module = 'vpa_sku_generator'
        WHERE module = 'product_sequence'
    """)

    print("✅ Module names fixed successfully!")
    print("   - partner-vat-number → partner_vat_number")
    print("   - product_sequence → vpa_sku_generator")
