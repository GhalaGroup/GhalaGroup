#!/usr/bin/env python3
import xmlrpc.client

# Connect to Odoo
url = 'http://localhost:8071'
db = 'odoo'
username = 'admin'
password = 'admin'

# Authenticate
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
print(f"Authenticated as UID: {uid}")

# Get models
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Check if logo field exists
fields = models.execute_kw(db, uid, password,
    'vpa.document.template', 'fields_get',
    [['logo', 'company_id', 'name']],
    {'attributes': ['string', 'type', 'relation', 'related']})

print(f"\nFields on vpa.document.template:")
for field_name, field_info in fields.items():
    print(f"  {field_name}: {field_info.get('string')} (type: {field_info.get('type')})")
    if field_info.get('related'):
        print(f"    related: {field_info.get('related')}")

# Read template with bin_size=False
template_data = models.execute_kw(db, uid, password,
    'vpa.document.template', 'read',
    [[3]],
    {'fields': ['name', 'logo', 'company_id'], 'context': {'bin_size': False}})

print(f"\nTemplate data:")
print(f"  Name: {template_data[0].get('name')}")
print(f"  Company: {template_data[0].get('company_id')}")
if 'logo' in template_data[0]:
    logo = template_data[0]['logo']
    if logo:
        print(f"  Logo: {len(logo)} bytes")
    else:
        print(f"  Logo: (empty)")
else:
    print(f"  Logo: (field not found)")

# Regenerate templates
print(f"\nRegenerating templates...")
result = models.execute_kw(db, uid, password,
    'vpa.document.template', 'action_regenerate_templates',
    [[3]])
print(f"Result: {result}")

# Check if QWeb templates were created
views = models.execute_kw(db, uid, password,
    'ir.ui.view', 'search_read',
    [[['key', 'like', '%vpa_template_3%']]],
    {'fields': ['id', 'name', 'key']})

print(f"\nQWeb templates created:")
for view in views:
    print(f"  ID {view['id']}: {view['name']} (key: {view['key']})")

if views:
    print("\n✓ SUCCESS: Templates regenerated with logo field!")
else:
    print("\n✗ ERROR: No templates found after regeneration")
