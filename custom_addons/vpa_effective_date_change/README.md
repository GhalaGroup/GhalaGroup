# VPA Effective Date Change

Professional stock transfer date management for Odoo 19 Enterprise.

## Overview

**VPA Effective Date Change** is a professional Odoo module that allows you to change the effective date of validated stock transfers with automatic synchronization of all related accounting and inventory records.

## Key Features

- **Pre-Validation Dating**: Set custom effective dates before validating stock transfers
- **Post-Validation Wizard**: Change dates of already validated transfers with smart wizard
- **Multi-Currency Support**: Automatic valuation recalculation for foreign currency purchases
- **Access Control**: Permission-based security for authorized users only
- **Automatic Synchronization**: Updates stock moves, journal entries, and valuation layers
- **Smart Validation**: Validates exchange rates and database integrity

## Installation

1. Copy this module to your Odoo addons directory
2. Update the apps list in Odoo
3. Install "VPA Effective Date Change" from Apps menu

## Configuration

1. Go to **Settings > Users & Companies > Groups**
2. Add users to "VPA: Change Effective Date" group
3. Users in this group can change effective dates

## Usage

### Method 1: Before Validation

1. Open any stock picking (delivery, receipt, internal transfer)
2. Set the "Effective Date" field to your desired date
3. Click "Validate" - the module will use your custom date

### Method 2: After Validation

1. Open a validated stock picking
2. Click "Change Effective Date" button
3. Select the new date in the wizard
4. Confirm - all related records update automatically

## What Gets Updated

When you change an effective date, the module automatically synchronizes:

- **Stock Records**: Stock Picking, Stock Moves, Stock Move Lines
- **Accounting**: Journal Entries, Journal Items, Account Reconciliation
- **Valuation**: Stock Valuation Layers, Product Costs (FIFO/Average), Foreign Currency Rates

## Technical Information

- **Module Name**: VPA Effective Date Change
- **Technical Name**: vpa_effective_date_change
- **Version**: 19.0.1.0.0
- **License**: OPL-1 (Odoo Proprietary License)
- **Author**: VPA Software Limited
- **Category**: Inventory/Inventory
- **Depends**: account_accountant, stock, sale_management, purchase

## Support

- **Email**: support@vpasoftware.com
- **Website**: https://www.vpasoftware.com
- **Response Time**: Within 24 hours on business days

## Copyright

Copyright © 2025 VPA Software Limited. All rights reserved.

This software is licensed under the Odoo Proprietary License v1.0.
See the LICENSE file for full copyright and licensing details.
