#!/usr/bin/env python3
import xmlrpc.client

url = "http://localhost:8071"
db = "Odoo19-Enterprise"
username = "admin"
password = "admin"

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print("="*80)
print("DEEP CHECK: PDF GENERATION CONFIGURATION")
print("="*80)

# 1. Check all paperformats
print("\n1. ALL PAPERFORMATS:")
paperformats = models.execute_kw(db, uid, password,
    'report.paperformat', 'search_read',
    [[]],
    {'fields': ['id', 'name', 'margin_top', 'margin_bottom', 'margin_left', 'margin_right', 'header_spacing', 'dpi']})

for pf in paperformats:
    print(f"\n  ID {pf['id']}: {pf['name']}")
    print(f"    Margins - T:{pf['margin_top']}, B:{pf['margin_bottom']}, L:{pf['margin_left']}, R:{pf['margin_right']}")
    print(f"    Header Spacing: {pf['header_spacing']}, DPI: {pf['dpi']}")

# 2. Check VPA templates
print("\n2. VPA DOCUMENT TEMPLATES:")
templates = models.execute_kw(db, uid, password,
    'vpa.document.template', 'search_read',
    [[]],
    {'fields': ['id', 'name', 'report_action_id']})

for tmpl in templates:
    print(f"\n  Template: {tmpl['name']} (ID: {tmpl['id']})")
    if tmpl['report_action_id']:
        report_id = tmpl['report_action_id'][0]

        # Get report action details
        report = models.execute_kw(db, uid, password,
            'ir.actions.report', 'read',
            [[report_id]],
            {'fields': ['name', 'report_name', 'paperformat_id', 'print_report_name']})

        if report:
            r = report[0]
            print(f"    Report Action ID: {report_id}")
            print(f"    Report Name: {r['report_name']}")

            if r['paperformat_id']:
                pf_id = r['paperformat_id'][0]
                pf_name = r['paperformat_id'][1]
                print(f"    Using Paperformat: {pf_name} (ID: {pf_id})")

                # Get detailed paperformat info
                pf_detail = models.execute_kw(db, uid, password,
                    'report.paperformat', 'read',
                    [[pf_id]],
                    {'fields': ['margin_top', 'margin_bottom', 'margin_left', 'margin_right', 'header_spacing']})

                if pf_detail:
                    print(f"    MARGINS: T:{pf_detail[0]['margin_top']}, B:{pf_detail[0]['margin_bottom']}, L:{pf_detail[0]['margin_left']}, R:{pf_detail[0]['margin_right']}")
                    print(f"    Header Spacing: {pf_detail[0]['header_spacing']}")
            else:
                print("    ⚠️  NO PAPERFORMAT ASSIGNED!")

# 3. Check if there are multiple report actions for sale.order
print("\n3. ALL REPORT ACTIONS FOR sale.order:")
all_reports = models.execute_kw(db, uid, password,
    'ir.actions.report', 'search_read',
    [[['model', '=', 'sale.order'], ['report_type', '=', 'qweb-pdf']]],
    {'fields': ['id', 'name', 'report_name', 'paperformat_id']})

for report in all_reports:
    print(f"\n  Report: {report['name']} (ID: {report['id']})")
    print(f"    Report Name: {report['report_name']}")
    if report['paperformat_id']:
        print(f"    Paperformat: {report['paperformat_id'][1]} (ID: {report['paperformat_id'][0]})")
    else:
        print(f"    ⚠️  No paperformat assigned")

# 4. Check company paperformat settings
print("\n4. COMPANY PAPERFORMAT:")
company = models.execute_kw(db, uid, password,
    'res.company', 'search_read',
    [[]],
    {'fields': ['id', 'name', 'paperformat_id'], 'limit': 1})

if company:
    c = company[0]
    print(f"  Company: {c['name']}")
    if c['paperformat_id']:
        print(f"  Default Paperformat: {c['paperformat_id'][1]} (ID: {c['paperformat_id'][0]})")
    else:
        print("  No default paperformat")

# 5. Check the QWeb template
print("\n5. QWEB TEMPLATE CHECK:")
templates = models.execute_kw(db, uid, password,
    'vpa.document.template', 'search_read',
    [[]],
    {'fields': ['id', 'name']})

for tmpl in templates:
    # Search for the QWeb view
    qweb_views = models.execute_kw(db, uid, password,
        'ir.ui.view', 'search_read',
        [[['name', 'ilike', f'report_template_{tmpl["id"]}'], ['type', '=', 'qweb']]],
        {'fields': ['id', 'name', 'key']})

    if qweb_views:
        print(f"\n  Template: {tmpl['name']}")
        for view in qweb_views:
            print(f"    QWeb View: {view['name']} (ID: {view['id']})")
            print(f"    Key: {view['key']}")

print("\n" + "="*80)
print("CHECK COMPLETE")
print("="*80)
