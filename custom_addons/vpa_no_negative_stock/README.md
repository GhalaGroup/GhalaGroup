# VPA Stock Sentinel (`vpa_no_negative_stock`)

Prevent negative stock in Odoo 19 Enterprise, under admin control.

## What it does

Odoo allows on-hand stock to go below zero by default. This module enforces
non-negative inventory at `stock.quant._update_available_quantity` — the single
point every stock decrement passes through — so deliveries, transfers,
manufacturing consumption, scrap, inventory adjustments and POS pickings are all
covered by one mechanism.

## Configuration

**Inventory → Settings → VPA Stock Sentinel** (per company):

- **Prevent Negative Stock** — master on/off (off by default).
- **Mode**:
  - *Hard Block* — the operation is stopped with a detailed error.
  - *Soft Warn (Manager Override)* — only an Inventory Manager can push it
    through, after entering a mandatory reason that is logged.
- **Alert Users** — users who receive a to-do activity when a block/override
  occurs.

## Exceptions (3 tiers)

An "Allow Negative Stock" flag can be set on:

- a **product** (Inventory tab),
- a **product category** (inherited by child categories),
- a **stock location**.

If any applies, negatives are permitted for that case.

## Inventory Adjustment Approval (optional)

A separate, optional control: require **manager approval** for manual inventory
adjustments (the "Update Quantity" / On-Hand count screen), increase or decrease.

**Inventory → Settings → VPA Stock Sentinel → Inventory Adjustment Approval**
(per company, off by default):

- **Require Approval for Inventory Adjustments** — when on, applying an
  adjustment opens a reason prompt and creates a **pending request** instead of
  changing stock.
- **Adjustment Approvers** — users who can approve/reject (falls back to
  Inventory Managers if empty).

Approvers review requests under **Inventory → Operations → Adjustment
Approvals**. On **Approve**, the captured change is applied. On **Reject**
(reason required), nothing changes. Everything is recorded with chatter.

Note: this gates manual inventory adjustments only — deliveries, receipts,
transfers and production are unaffected.

## Reporting

- **Inventory → Reporting → Stock Sentinel Log** — every block/warn/override.
- **Inventory → Reporting → Currently Negative Stock** — products already
  negative, to clean up before enabling enforcement.
- **Inventory → Operations → Adjustment Approvals** — pending/approved/rejected
  adjustment requests.

## License

OPL-1 — Copyright (C) 2025 VPA Solutions Limited — info@vpa.co.tz
