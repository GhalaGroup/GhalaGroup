#!/usr/bin/env python3
"""Regenerate VPA template via Odoo RPC"""
import xmlrpc.client

url = 'http://172.21.0.3:8069'
db = 'odoo'
username = 'admin'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Get template 3
template_id = 3
template_name = models.execute_kw(db, uid, password,
    'vpa.document.template', 'read',
    [[template_id], ['name', 'header_show_circle', 'footer_show_shape']])

print(f"Template: {template_name}")

# Regenerate template
try:
    result = models.execute_kw(db, uid, password,
        'vpa.document.template', 'action_regenerate_templates',
        [[template_id]])
    print("SUCCESS: Templates regenerated!")
    print(f"Result: {result}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
