#!/usr/bin/env python3
import odoo
from odoo import api
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf', '-d', 'odoo'])

registry = Registry('odoo')
with registry.cursor() as cr:
    env = api.Environment(cr, odoo.SUPERUSER_ID, {'bin_size': False})

    template = env['vpa.document.template'].browse(3)
    print(f"Template: {template.name}")
    print(f"Logo size: {len(template.logo) if template.logo else 0} bytes")

    # Force compute preview
    template._compute_preview()

    # Get preview HTML
    preview_html = template.preview

    # Check if logo is in preview
    if 'data:image' in preview_html:
        print("\n✓ SUCCESS: Preview contains data URI image (logo is embedded)!")
        # Count how many data URIs
        count = preview_html.count('data:image')
        print(f"  Found {count} embedded image(s)")
    else:
        print("\n✗ ERROR: Preview does not contain data URI image")

    # Check for broken image references
    if '/web/image' in preview_html:
        print("  ⚠ Warning: Found /web/image URL (may not work in iframe)")

    # Save preview to file for inspection
    with open('/tmp/preview_output.html', 'w') as f:
        f.write(preview_html)
    print("\nPreview saved to /tmp/preview_output.html")

    # Show first 500 chars of preview
    print("\nPreview excerpt:")
    print(preview_html[:500])
