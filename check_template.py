#!/usr/bin/env python3
"""Check what's in the generated VPA template"""
import xmlrpc.client

url = 'http://localhost:8071'
db = 'odoo'
username = 'admin'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Get all VPA templates
templates = models.execute_kw(db, uid, password,
    'vpa.document.template', 'search_read',
    [[]], {'fields': ['id', 'name']})

print(f"Found {len(templates)} VPA templates:")
for t in templates:
    print(f"  - Template {t['id']}: {t['name']}")

    # Get the generated view
    views = models.execute_kw(db, uid, password,
        'ir.ui.view', 'search_read',
        [[('key', '=', f"vpa_document_layout.external_layout_vpa_template_{t['id']}")]],
        {'fields': ['id', 'name', 'arch'], 'limit': 1})

    if views:
        view = views[0]
        arch = view['arch']

        # Check for footer content
        has_footer_wave = 'footer-wave' in arch or 'Footer Wave' in arch
        has_footer_cell = 'footer-cell' in arch
        has_footer_content = 'footer-content' in arch

        print(f"    View ID: {view['id']}")
        print(f"    Has footer-wave: {has_footer_wave}")
        print(f"    Has footer-cell: {has_footer_cell}")
        print(f"    Has footer-content: {has_footer_content}")

        # Show last 500 chars
        print(f"    Last 500 chars of arch:")
        print(f"    {arch[-500:]}")
        print()
