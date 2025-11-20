#!/usr/bin/env python3
import xmlrpc.client

# Odoo connection details
url = "http://localhost:8071"
db = "Odoo19-Enterprise"
username = "admin"
password = "admin"

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print(f"Connected as user ID: {uid}")

# Find ALL paperformats
all_paperformats = models.execute_kw(db, uid, password,
    'report.paperformat', 'search_read',
    [[]],
    {'fields': ['id', 'name', 'margin_top', 'margin_bottom', 'margin_left', 'margin_right']})

print(f"\nAll paperformats:")
for pf in all_paperformats:
    print(f"  ID {pf['id']}: {pf['name']} - margins: T:{pf['margin_top']}, B:{pf['margin_bottom']}, L:{pf['margin_left']}, R:{pf['margin_right']}")

# Find VPA A4 paperformat
paperformat_ids = models.execute_kw(db, uid, password,
    'report.paperformat', 'search',
    [[['name', '=', 'VPA A4']]])

if paperformat_ids:
    print(f"\nFound VPA A4 paperformat: {paperformat_ids[0]}")

    # Update with zero margins
    models.execute_kw(db, uid, password,
        'report.paperformat', 'write',
        [[paperformat_ids[0]], {
            'margin_top': 0,
            'margin_bottom': 0,
            'margin_left': 0,
            'margin_right': 0,
            'header_spacing': 0,
        }])
    print("Updated paperformat with zero margins")

    # Read back to verify
    paperformat = models.execute_kw(db, uid, password,
        'report.paperformat', 'read',
        [[paperformat_ids[0]], ['margin_top', 'margin_bottom', 'margin_left', 'margin_right', 'header_spacing']])
    print(f"Paperformat margins: {paperformat[0]}")
else:
    print("\nVPA A4 paperformat not found")

# Find and regenerate all VPA templates
try:
    template_ids = models.execute_kw(db, uid, password,
        'vpa.document.template', 'search',
        [[]])

    print(f"Found {len(template_ids)} templates")

    for template_id in template_ids:
        template = models.execute_kw(db, uid, password,
            'vpa.document.template', 'read',
            [[template_id], ['name']])
        print(f"Regenerating template: {template[0]['name']}")

        # Trigger save to regenerate
        models.execute_kw(db, uid, password,
            'vpa.document.template', 'write',
            [[template_id], {'name': template[0]['name']}])
except Exception as e:
    print(f"Template model not found or error: {e}")

print("Done!")
