#!/usr/bin/env python3
"""
Script to fix the company variable issue in VPA templates by:
1. Deleting existing template views
2. Recreating them with the company fix
"""

import xmlrpc.client

# Connection details
url = 'http://localhost:8070'
db = 'udtz_beta'
username = 'admin'
password = 'admin'

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print(f"Connected to {db} as user {uid}")

# Find VPA - Quote Template
template_id = models.execute_kw(db, uid, password,
    'vpa.document.template', 'search',
    [[('name', '=', 'VPA - Quote Template')]])

if not template_id:
    print("ERROR: Template not found!")
    exit(1)

template_id = template_id[0]
print(f"Found template ID: {template_id}")

# Find and delete existing views
view_keys = [
    f'vpa_document_layout.report_template_{template_id}',
    f'vpa_document_layout.external_layout_vpa_template_{template_id}'
]

for key in view_keys:
    view_ids = models.execute_kw(db, uid, password,
        'ir.ui.view', 'search',
        [[('key', '=', key)]])

    if view_ids:
        print(f"Deleting view {key} (ID: {view_ids[0]})")
        models.execute_kw(db, uid, password,
            'ir.ui.view', 'unlink',
            [view_ids])
    else:
        print(f"View {key} not found (will be created)")

# Recreate the QWeb templates
print(f"\nRecreating QWeb templates for template {template_id}...")
models.execute_kw(db, uid, password,
    'vpa.document.template', '_create_qweb_template',
    [[template_id]])

print("\nVerifying company fix...")
view_id = models.execute_kw(db, uid, password,
    'ir.ui.view', 'search',
    [[('key', '=', f'vpa_document_layout.external_layout_vpa_template_{template_id}')]])

if view_id:
    view = models.execute_kw(db, uid, password,
        'ir.ui.view', 'read',
        [view_id[0], ['arch_db']])

    if 'company if company is defined else env.company' in str(view[0]['arch_db']):
        print("✓ Company fix IS present in recreated template!")
    else:
        print("✗ Company fix NOT found in recreated template")
        print("First 500 chars of arch:")
        print(str(view[0]['arch_db'])[:500])
else:
    print("ERROR: View not created!")

print("\nDone! Please restart Odoo container to clear QWeb cache:")
print("  docker restart ud_odoo19")
