# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA Production Commission',
    'version': '19.0.2.0.9',
    'category': 'Manufacturing/Commission',
    'summary': 'Complete production commission lifecycle: approval, guarantee & true-up billing, multi-currency payments (v2.0.1)',
    'description': """
VPA Production Commission
=========================

Commission management system based on Manufacturing Order completion.
Commission is calculated from commissionable raw materials consumed during production.

Key Features
------------
* **Per-Employee Schemes**: Each employee has individual commission rates and minimum guarantees
* **MO-Based Commission**: Automatic calculation when Manufacturing Orders are completed
* **Commission History**: View and use historical base amounts from previous MOs for same product
* **Commissionable Products**: Mark specific raw materials to be included in commission calculation
* **MO Filtering**: Configure which MOs apply per scheme (all, workcenter, category, products)
* **Minimum Guarantee**: Annual minimum with monthly/quarterly tracking
* **Approval Workflow**: Pending -> Confirmed -> Paid status tracking
* **High Security**: Strict access control - Commission Managers only
* **Search Panel**: Side panel with Status and Employee filters
* **Pivot & Graph Views**: Export to Excel, visual commission analysis
* **User Access Rights**: Privilege-based access in User form

Version History
---------------
* **19.0.2.0.9** - Not Applicable badge shown in red

* **19.0.2.0.8** - Advance payments
  - Pay wizard: new "Advance Payment" option to deliberately pay beyond the
    guarantee/confirmed ceiling (e.g. years without a minimum guarantee, or
    advances before approval). No bill required - the payment is year-linked
    and applies against future bills
  - Pay button now available on any open year

* **19.0.2.0.7** - Manual commission auto-calculation
  - Add Manual Commission: the rate now auto-fills from the commission year
    matching the chosen date (respects per-year rates), and the amount is
    calculated automatically from base x rate (still overridable)

* **19.0.2.0.6** - Repair legacy MO commission statuses
  - MOs carrying obsolete status values ('blocked', 'pending') from early
    versions displayed an empty Commission badge and matched no filter;
    statuses are recomputed from the actual data on upgrade

* **19.0.2.0.5** - Not Applicable status refresh
  - Commission by MO: marking/unmarking Not Applicable now refreshes the list
    immediately (the status changed in the database but the screen kept
    showing the old value until a manual reload)

* **19.0.2.0.4** - Editable per-year rate
  - The yearly Rate (%) is now a real per-year value: prefilled with the scheme
    default when adding a year, freely editable (e.g. 5% for 2023)
  - Existing years automatically backfilled from their scheme default

* **19.0.2.0.1** - Hotfixes for fresh installations
  - Fix: "Add a line" missing in Yearly Rates (embedded the editable list inline;
    the previous external view reference was silently ignored by Odoo and the
    read-only Commission Centre list was rendered instead)
  - Fix: field tracking removed from scheme year (blocked non-admin managers
    from editing years due to mail tracking access rights)
  - Add explicit 'mail' dependency (chatter on commission years)
  - Distinct internal field labels (removes duplicate-label warnings)

* **19.0.2.0.0** - Major Release: Complete Commission Lifecycle
  - Commission Centre: kanban dashboard per employee-year with drill-down to MOs/SOs
  - Approval workflow: per-line Approve/Reject, bulk confirm, full timestamps & user trail
  - Guarantee advance billing: one bill, expense spread over 12 months (prepaid accounting)
  - Excess (true-up) billing: confirmed commission above guarantee, expense recognised
    in the months the commission was generated, explicit guarantee offset
  - Year-linked payments: multi-currency (USD/TZS) with live exchange rate,
    payment-on-account with later linking, auto-reconciliation against bills
  - Rounding write-offs: pay clean amounts, small differences booked automatically
  - Commission Payment Voucher (VPA-styled PDF) with USD equivalents
  - Journal transaction pre-creation for cash journals (reconcile-only workflow)
  - Change Commission Date wizard (single/bulk, audit trail, old->new display)
  - Close/Reopen year with mandatory reason and chatter audit log
  - Pay ceiling: only guarantee + confirmed commission is payable
  - Group by Client / Customer Reference; delivered flag for origin-linked MOs
  - Security hardening: own-records rules, company isolation, field-level
    protection of compensation data, per-user compute caching

* **19.0.1.1.0** - Commission History Feature
  - Historical base amounts from past MOs for same product
  - Compare and use previous commission calculations
  - Override base amount with historical values
  - Audit trail for historical base amount usage
  - Smart detection of product-specific history

* **19.0.1.0.0** - Initial release for Odoo 19
  - Per-employee commission schemes
  - Production commission on MO completion
  - Commissionable product flag
  - Configurable MO filters
  - Minimum guarantee system
  - Approval workflow
  - Search panel with Status and Employee filters
  - Pivot view for commission analysis with Excel export
  - Graph view for visual reporting
  - Privilege-based user access (Sales Commission section in user form)
  - Date filter with year/month/quarter selection

Developed by VPA Solutions Limited
Support: info@vpa.co.tz
    """,
    'author': 'VPA Solutions Limited',
    'website': 'https://www.vpa.co.tz',
    'support': 'info@vpa.co.tz',
    'license': 'OPL-1',
    'price': 499.00,
    'currency': 'USD',
    'depends': [
        'mail',
        'mrp',
        'hr',
        'sale',
        'sale_mrp',
        'account',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'wizard/commission_generate_wizard_views.xml',
        'wizard/commission_payment_wizard_views.xml',
        'wizard/commission_statement_wizard_views.xml',
        'wizard/commission_bill_wizard_views.xml',
        'wizard/commission_year_summary_wizard_views.xml',
        'wizard/manual_commission_wizard_views.xml',
        'wizard/adjust_materials_wizard_views.xml',
        'wizard/commission_change_date_wizard_views.xml',
        'report/commission_payment_voucher.xml',
        'wizard/commission_pay_year_wizard_views.xml',
        'report/commission_statement_report.xml',
        'report/commission_statement_template.xml',
        'views/vpa_commission_scheme_year_views.xml',
        'views/vpa_commission_scheme_views.xml',
        'views/vpa_commission_line_views.xml',
        'views/product_template_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_production_commission_report_views.xml',
        'views/so_commission_report_views.xml',
        'views/hr_employee_views.xml',
        'views/res_config_settings_views.xml',
        'views/menuitems.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
