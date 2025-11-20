#!/usr/bin/env python3
import xmlrpc.client

url = 'http://localhost:8071'
db = 'Odoo19-Enterprise'
username = 'admin'
password = 'admin'

# Authenticate
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
print(f"Logged in as user {uid}")

# Get models proxy
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Get template 1
template = models.execute_kw(db, uid, password,
    'vpa.document.template', 'read',
    [[1], ['name', 'report_action_id', 'paper_size', 'paper_orientation']])

print(f"\nTemplate: {template[0]['name']}")
print(f"Paper: {template[0]['paper_size']} {template[0]['paper_orientation']}")
print(f"Report Action ID: {template[0]['report_action_id']}")

# Get a sale order to render
order_ids = models.execute_kw(db, uid, password,
    'sale.order', 'search', [[]], {'limit': 1})

if order_ids:
    print(f"\nUsing sale order ID: {order_ids[0]}")

    # Get report action
    report = models.execute_kw(db, uid, password,
        'ir.actions.report', 'read',
        [[template[0]['report_action_id'][0]], ['report_name', 'paperformat_id']])

    print(f"Report name: {report[0]['report_name']}")
    print(f"Paperformat ID: {report[0]['paperformat_id']}")

    # Try to render HTML
    print("\nRendering HTML...")
    try:
        html_result = models.execute_kw(db, uid, password,
            'ir.actions.report', '_render_qweb_html',
            [template[0]['report_action_id'][0], order_ids])

        html_content = html_result[0] if isinstance(html_result, tuple) else html_result
        print(f"HTML size: {len(html_content)} bytes")

        # Save to file
        with open('/tmp/preview_html.html', 'wb') as f:
            f.write(html_content if isinstance(html_content, bytes) else html_content.encode())
        print("HTML saved to /tmp/preview_html.html")

    except Exception as e:
        print(f"Error: {e}")
else:
    print("No sale orders found!")
