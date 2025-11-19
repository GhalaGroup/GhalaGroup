#!/usr/bin/env python3
import xmlrpc.client

url = 'http://localhost:8071'
db = 'odoo'
username = 'admin'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

if not uid:
    print("Authentication failed")
    exit(1)

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Get template ID 3
template_id = 3

# Call _create_qweb_template
print(f"Recreating QWeb templates for template {template_id}...")
try:
    models.execute_kw(db, uid, password,
        'vpa.document.template', '_create_qweb_template',
        [[template_id]])
    print("Success! Templates recreated.")
except Exception as e:
    print(f"Error: {e}")
