# -*- coding: utf-8 -*-
# Part of VPA Tanzania Localization. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2025 VPA Software Limited
{
    'name': 'VPA Tanzania Localization',
    'version': '19.0.1.0.1',
    'category': 'Localization',
    'summary': 'Tanzania localization with TIN and VRN tax identification numbers',
    'description': """
VPA Tanzania Localization
=========================

Complete localization module for Tanzanian businesses with TRA (Tanzania Revenue Authority) compliance.

Key Features
------------
* **Separate TIN and VRN Fields**: Proper handling of Tax Identification Number (TIN) and VAT Registration Number (VRN)
* **Format Validation**: Ensures TIN and VRN follow Tanzanian formats
* **Unique Constraints**: Prevents duplicate tax numbers in the system
* **Audit Trail**: Track changes to tax identification numbers
* **Journal Auto-Correction**: Automatically assigns correct journal types for purchase documents
* **TRA Compliance**: Follows Tanzania Revenue Authority guidelines

Tax Number Formats
-------------------
* **TIN (Taxpayer Identification Number)**: 9-digit format (123-456-789)
  - Used for: All taxpayers registered with TRA
  - Required for: Business transactions, tax filing

* **VRN (VAT Registration Number)**: 10-character format (40-XXXXXX-X)
  - Used for: VAT-registered businesses
  - Format: Starts with "40" (TZ VAT prefix) + 6 digits + 1 check character
  - Required for: VAT invoices, VAT returns

Features in Detail
------------------
1. **Partner Management**:
   - Separate TIN and VRN fields on partner/customer records
   - Validation for Tanzanian tax number formats
   - Unique constraints prevent duplicate registrations
   - Field tracking for audit compliance

2. **Accounting Integration**:
   - Smart journal assignment for purchase documents
   - Automatic currency handling for multi-currency transactions
   - Proper journal type validation

3. **Compliance**:
   - TRA-compliant field labels and formats
   - Audit trail for tax number changes
   - Help text for users explaining TIN vs VRN

Use Cases
---------
* Tanzanian businesses requiring TRA-compliant invoicing
* Companies managing both TIN and VRN registrations
* Multi-currency businesses operating in Tanzania
* Organizations needing tax number validation and tracking

Technical Details
-----------------
* Extends: res.partner, account.move
* Database: Adds vrn field to res_partner table
* Constraints: SQL-level unique constraints on TIN and VRN
* Compatible with: Odoo 19.0 Enterprise Edition

License
-------
Odoo Proprietary License v1.0 (OPL-1)
This module is proprietary software. Use requires a valid Odoo Enterprise subscription.
Redistribution and resale are prohibited.

Support
-------
For support, customization, or feature requests:
* Email: support@vpasoftware.com
* Website: https://www.vpasoftware.com

Author: VPA Software Limited
Copyright (C) 2025 VPA Software Limited
    """,
    'author': 'VPA Software Limited',
    'website': 'https://www.vpasoftware.com',
    'license': 'OPL-1',
    'price': 29.99,
    'currency': 'USD',
    'depends': ['base', 'account', 'contacts', 'sale'],

    'pre_init_hook': 'pre_init_hook',

    'data': [
        'security/ir.model.access.csv',
        'data/tanzania_regions_wards.xml',
        'data/tanzania_detailed_wards.xml',
        'data/tanzania_complete_wards.xml',
        'data/update_wards_to_districts.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
