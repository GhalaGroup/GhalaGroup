# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.
{
    'name': 'VPA Production Commission',
    'version': '19.0.2.3.2',
    'category': 'Manufacturing/Commission',
    'summary': 'Complete production commission lifecycle: approval, guarantee & true-up billing, multi-currency payments (v2.3.2)',
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
* **19.0.2.3.2** - Pay wizard caps at the year's outstanding; unassign payments
  - Paying more than the year needs no longer overpays it: the payment is
    created on account and an allocation applies exactly the outstanding;
    the remainder stays unallocated ("Not allocated" block), applicable to
    any year later. Exception: "Write Off the Difference" still applies the
    full amount (close-it-clean path). Advances on a covered year go fully
    on account
  - Unassigning: clearing a payment's Commission Year (or deleting an
    allocation) is logged in the year's chatter with payment and amount
  - Closed-year protection both ways: payments cannot be assigned to or
    unassigned from a closed year without reopening it

* **19.0.2.3.1** - Cancelled MOs are automatically Not Applicable
  - Cancelling a Manufacturing Order now cancels its PENDING commission
    lines automatically (confirmed/paid lines stay - manager decision) and
    the MO's commission status computes to Not Applicable by itself
  - Generate Commission is refused on cancelled MOs
  - Migration applies the same to MOs cancelled before the upgrade - no
    more pressing "Mark Not Applicable" on old cancelled orders

* **19.0.2.3.0** - On-account allocation workflow, Total to Pay card, hardening
  - Year cards: amber "Not allocated" block whenever the employee has
    on-account money not applied to any year, with a one-click Allocate
    action (hidden on settled years; invisible spacer keeps equal heights)
  - Apply Payment wizard rewritten as a reconciliation-style table: tick the
    payments to apply, per-row amounts prefilled with the unallocated
    remainder, live Total to Apply / Outstanding After, multi-apply in one
    click. Strict validation: non-positive amounts on ticked rows are
    rejected, never silently skipped
  - Card redesign around plain language: Min. year commission (with USD
    reference in the subtitle) as info, Total to Pay = max(guarantee, total
    earned incl. pending) as the headline, Already Paid, Still to Pay.
    Earned panel bar shows green (within guarantee) / white (above the
    minimum) / red (below); payment bar shows cleared / pending
    reconciliation / white overpaid tail. Fully settled years swap the Pay
    button for Close Year
  - Commission Payments list: "Allocated To" (years + amounts via
    allocations) and "On Account" (unallocated remainder) columns
  - Commission fields on the payment form now appear only for commission
    payments (vendor is a commission employee, or the payment already
    carries a year/allocations) - never on ordinary vendor payments
  - True-up bills numbered per run (#2, #3...) via a structural flag -
    stable under translation and cancellations; monthly deferral entries
    carry the numbered ref
  - Hardening: allocations into a closed year are blocked; reset-to-pending
    respects the year lock and clears the close marker; migration backfills
    paid_by_close for years closed under v2.1.x so reopening them reverts
    correctly; card totals currency-rounded (FX residues no longer block the
    Close Year button); Commission Centre computes batched (one payment
    query per page instead of one per card)

* **19.0.2.2.0** - Cleared vs issued payments, symmetric close/reopen
  - Year card: "pending reconciliation" under Already Paid, and a split
    progress bar (green = reconciled, striped amber = issued awaiting bank).
    Paid still counts issued payments - the meaning of Outstanding is unchanged
  - New fields Paid (Cleared) / Issued Not Cleared on the commission year
  - Closing a settled year stamps the lines it flips to paid (paid_by_close);
    reopening now reverts exactly those lines to confirmed. Previously reopen
    left every line claiming paid, so an open year could carry paid lines
    backed by a settlement that had been reopened

* **19.0.2.1.2** - Fix: payment form blocked for users without commission access
  - The readonly modifier on the standard payment_type field named
    commission_allocation_ids. The web client fetches whatever a modifier
    references, so every user without commission rights hit AccessError when
    opening or saving ANY payment - no server-side sudo could prevent it,
    because the client was doing the read. Test a sudo-computed boolean instead

* **19.0.2.1.1** - Distinct label for Payment Currency
  - payment_currency_id inherited "Currency" from its related field and
    collided with currency_id on the Apply Payment wizard

* **19.0.2.1.0** - Commission per item, closed-year protection, clearer year card
  - Commission Per Item on the Generate wizard, the commission line form and
    list, and the Commission by MO report (averaged, not summed, in the pivot)
  - Materials lists gained a Commissionable total: the plain sum counted
    excluded lines and contradicted the Base Amount beside it
  - Closing a year now blocks new commission from landing in it; previously
    only the lines existing at close were locked, so an MO processed later
    silently moved a reconciled year's totals
  - Commission year card rewritten in plain language (what he earned / what we
    pay him) with the payable amount tagged guarantee or approved
  - Fix: the payment form raised AccessError for every user without commission
    rights, because an invisible field on the standard form read the commission
    scheme and allocations unprivileged

* **19.0.2.0.11** - Manual commission in the Generate wizard
  - New "Manual Commission" checkbox: tick to edit the Total Commission,
    per-employee amount or rate directly (all stay in sync, generated
    amounts match exactly what was typed); untick resets to standard rates
  - "Extra vs Standard" shown at the top and per employee: how much above
    (or below) the standard year rate the commission is
  - Rates carry full precision so manually entered amounts are exact

* **19.0.2.0.10** - Change history restored on commission years
  - Rate, Minimum Guarantee and State changes are logged again in the year's
    chatter (old value -> new value, user, timestamp). Verified compatible
    with commission-manager editing

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
        'wizard/commission_apply_payment_wizard_views.xml',
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
