#!/usr/bin/env python3
"""Force regeneration of VPA Document Template"""
import xmlrpc.client

# Odoo connection details
url = 'http://localhost:8069'
db = 'odoo'
username = 'admin'
password = 'admin'

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

if uid:
    print(f"✓ Authenticated as user ID: {uid}")

    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    # Find all VPA templates
    template_ids = models.execute_kw(db, uid, password,
        'vpa.document.template', 'search', [[]])

    print(f"Found {len(template_ids)} template(s)")

    # Force regeneration by toggling a field
    for template_id in template_ids:
        print(f"\nRegenerating template {template_id}...")

        # Read current footer_show_shape value
        template = models.execute_kw(db, uid, password,
            'vpa.document.template', 'read', [template_id],
            {'fields': ['footer_show_shape', 'name']})

        if template:
            name = template[0]['name']
            current_value = template[0]['footer_show_shape']
            print(f"  Template: {name}")
            print(f"  Current footer_show_shape: {current_value}")

            # Toggle and save to force regeneration
            models.execute_kw(db, uid, password,
                'vpa.document.template', 'write',
                [template_id, {'footer_show_shape': not current_value}])
            print(f"  ✓ Toggled to {not current_value}")

            # Toggle back
            models.execute_kw(db, uid, password,
                'vpa.document.template', 'write',
                [template_id, {'footer_show_shape': current_value}])
            print(f"  ✓ Restored to {current_value}")
            print(f"  ✓ Template regenerated!")

    print("\n✓ All templates regenerated successfully!")
else:
    print("✗ Authentication failed")
