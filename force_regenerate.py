#!/usr/bin/env python3
"""Force regenerate all VPA templates by deleting ALL related views"""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')

import odoo
from odoo import api, SUPERUSER_ID

# Initialize Odoo
odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf'])

dbname = 'odoo'

with odoo.api.Environment.manage():
    registry = odoo.registry(dbname)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        print("=" * 80)
        print("FORCE REGENERATING ALL VPA TEMPLATES")
        print("=" * 80)

        # Find all VPA templates
        templates = env['vpa.document.template'].search([])
        print(f"\nFound {len(templates)} VPA templates:")
        for t in templates:
            print(f"  - Template {t.id}: {t.name}")

        # Find ALL views related to VPA templates
        all_views = env['ir.ui.view'].search([
            '|', '|', '|',
            ('key', 'like', '%vpa_template%'),
            ('key', 'like', '%template_%'),
            ('key', 'like', '%inherit_%'),
            ('name', 'like', '%VPA%')
        ])

        print(f"\n Found {len(all_views)} VPA-related views in database:")
        for v in all_views:
            print(f"  - View {v.id}: {v.name} (key: {v.key})")
            # Check if it has footer content
            if 'footer-wave' in (v.arch or '') or 'footer-cell' in (v.arch or ''):
                print(f"    ⚠️  THIS VIEW HAS FOOTER CONTENT!")

        print("\nDeleting all VPA template views...")
        all_views.unlink()
        print(f"✅ Deleted {len(all_views)} views")

        print("\nRegenerating templates...")
        for t in templates:
            print(f"  Regenerating template {t.id}: {t.name}")
            t._create_qweb_template()

        # Check what was created
        new_views = env['ir.ui.view'].search([
            '|', '|',
            ('key', 'like', '%template_%'),
            ('key', 'like', '%inherit_%'),
            ('name', 'like', '%VPA%')
        ])

        print(f"\n✅ Created {len(new_views)} new views:")
        for v in new_views:
            print(f"  - View {v.id}: {v.name} (key: {v.key})")
            # Check if it has footer content
            arch_str = str(v.arch or '')
            has_footer = 'footer-wave' in arch_str or 'footer-cell' in arch_str
            if has_footer:
                print(f"    ⚠️  WARNING: NEW VIEW STILL HAS FOOTER CONTENT!")
            else:
                print(f"    ✅ No footer content (correct!)")

        cr.commit()
        print("\n" + "=" * 80)
        print("REGENERATION COMPLETE!")
        print("=" * 80)
