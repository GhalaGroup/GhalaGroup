#!/usr/bin/env python3
import xmlrpc.client

url = "http://localhost:8071"
db = "Odoo19-Enterprise"
username = "admin"
password = "admin"

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Get the QWeb template content
qweb_views = models.execute_kw(db, uid, password,
    'ir.ui.view', 'search_read',
    [[['key', '=', 'vpa_document_layout.report_template_1']]],
    {'fields': ['id', 'name', 'arch_db']})

if qweb_views:
    view = qweb_views[0]
    print(f"QWeb Template: {view['name']}")
    print("\nSearching for margin/padding styles in template:")
    print("="*80)

    arch = view['arch_db']

    # Look for margin/padding in styles
    import re

    # Find all style attributes
    style_matches = re.findall(r'style="([^"]*)"', arch)

    found_margins = False
    for i, style in enumerate(style_matches, 1):
        if 'margin' in style.lower() or 'padding' in style.lower():
            print(f"\nStyle {i}: {style}")
            found_margins = True

    if not found_margins:
        print("\nNo inline margin/padding styles found in template")

    # Check for page-specific styles
    if '@page' in arch:
        print("\n\n@page rules found:")
        page_matches = re.findall(r'@page\s*{([^}]*)}', arch, re.DOTALL)
        for page in page_matches:
            print(f"  {page.strip()}")

    # Check for body styles
    if 'body' in arch:
        print("\n\nbody styles:")
        body_matches = re.findall(r'body\s*{([^}]*)}', arch, re.DOTALL)
        for body in body_matches:
            print(f"  {body.strip()}")

    # Save full template to file for inspection
    with open('/tmp/qweb_template.xml', 'w') as f:
        f.write(arch)
    print(f"\n\nFull template saved to: /tmp/qweb_template.xml")
else:
    print("QWeb template not found!")
