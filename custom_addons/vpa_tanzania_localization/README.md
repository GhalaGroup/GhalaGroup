# VPA Tanzania Localization

Complete localization module for Tanzanian businesses with TRA (Tanzania Revenue Authority) compliance.

## Features

### 🇹🇿 Tanzania-Specific Tax Numbers

- **TIN (Taxpayer Identification Number)**
  - 9-digit format: `123-456-789`
  - Required for all businesses registered with TRA
  - Unique constraint prevents duplicates
  - Format validation for Tanzanian partners

- **VRN (VAT Registration Number)**
  - 10-character format: `40-XXXXXX-X`
  - Starts with "40" (Tanzania VAT prefix)
  - Required only for VAT-registered businesses
  - Unique constraint prevents duplicates
  - Format validation for Tanzanian partners

### 📋 Key Capabilities

1. **Separate TIN and VRN Fields**
   - Clear distinction between TIN and VRN on partner records
   - Proper field labels following TRA terminology
   - Help text explaining each field's purpose

2. **Data Validation**
   - Automatic format validation for TZ partners
   - Real-time error messages with format examples
   - Prevents invalid tax numbers from being saved

3. **Audit Trail**
   - Track all changes to TIN and VRN fields
   - See who changed tax numbers and when
   - Essential for compliance and auditing

4. **Smart Journal Assignment**
   - Automatically assigns correct journal types for invoices/bills
   - Handles multi-currency purchase documents
   - Prevents common journal type errors

5. **Database Integrity**
   - SQL-level unique constraints on TIN and VRN
   - Prevents duplicate tax registrations
   - Maintains data consistency

## Installation

### Requirements

- Odoo 19.0 Enterprise Edition
- Modules: `base`, `account`, `contacts`
- PostgreSQL 12+

### Steps

1. **Download the Module**
   ```bash
   cd /path/to/odoo/addons
   # Place vpa_tanzania_localization folder here
   ```

2. **Update Apps List**
   - Go to Apps menu
   - Click "Update Apps List"
   - Search for "VPA Tanzania Localization"

3. **Install**
   - Click "Install" button
   - Module will create VRN field automatically
   - Existing TIN data is preserved

4. **Configure (Optional)**
   - Go to Contacts
   - Open any partner/customer
   - Set Country to "Tanzania"
   - Fill in TIN and/or VRN fields

## Usage

### Adding Tax Numbers to Partners

1. **Navigate to Contacts**
   - Open Contacts app
   - Select or create a partner

2. **Set Country**
   - Set Country to "Tanzania" for validation to work

3. **Enter TIN**
   - Field: TIN (Taxpayer ID)
   - Format: 9 digits (e.g., `123-456-789` or `123456789`)
   - System will normalize format automatically

4. **Enter VRN (if VAT registered)**
   - Field: VRN (VAT Registration Number)
   - Format: 10 characters starting with "40" (e.g., `40-1234567-X`)
   - Only visible for companies (not individuals)

### Validation Examples

**Valid TIN Formats:**
```
123456789
123-456-789
123 456 789
```

**Valid VRN Formats:**
```
401234567X
40-1234567-X
40 1234567 X
```

**Invalid Formats:**
```
12345      (Too short)
ABC123456  (Contains letters in TIN)
301234567X (VRN must start with 40)
```

## Tax Number Formats Explained

### TIN (Taxpayer Identification Number)

**Who needs it:**
- All businesses registered with TRA
- Self-employed individuals
- Companies and organizations

**Format:**
- 9 digits only
- No letters or special characters
- Example: `123-456-789`

**When to use:**
- Business registration
- Tax filing and returns
- All business transactions
- Bank account opening

### VRN (VAT Registration Number)

**Who needs it:**
- Businesses registered for VAT with TRA
- Companies with turnover > TZS 100M (threshold may vary)
- Voluntary VAT registrants

**Format:**
- Total 10 characters
- Starts with "40" (Tanzania code)
- Followed by 7 digits
- Ends with 1 alphanumeric check character
- Example: `40-1234567-X`

**When to use:**
- VAT invoices
- VAT returns and filing
- Claiming input VAT
- Cross-border transactions

## Troubleshooting

### Error: "TIN must be unique"

**Cause:** Another partner already has this TIN number

**Solution:**
1. Search for existing partner with same TIN
2. Update existing record or use different TIN
3. Contact support if TIN is genuinely yours

### Error: "Invalid TIN format"

**Cause:** TIN doesn't match Tanzanian 9-digit format

**Solution:**
1. Ensure TIN has exactly 9 digits
2. Remove any letters or special characters
3. Example: Change `TIN-123-456` to `123456789`

### Error: "Invalid VRN format"

**Cause:** VRN doesn't match Tanzanian format

**Solution:**
1. Ensure VRN starts with "40"
2. Ensure total length is 10 characters
3. Check last character is alphanumeric
4. Example: `40-1234567-X` ✓ not `20-1234567-X` ✗

### VRN field not visible

**Cause:** Partner is not set as a company

**Solution:**
1. Open partner record
2. Check "Is a Company" checkbox
3. VRN field will appear

### OWL Error: "vrn field is undefined"

**Cause:** Old `partner_vat_number` module conflicts

**Solution:**
1. Uninstall `partner_vat_number` module completely
2. Restart Odoo server
3. Install `vpa_tanzania_localization`
4. The new module replaces the old one

## Technical Details

### Database Changes

**New Fields:**
```sql
-- res_partner table
vrn VARCHAR (VAT Registration Number)
```

**Constraints:**
```sql
ALTER TABLE res_partner ADD CONSTRAINT vat_uniq UNIQUE (vat);
ALTER TABLE res_partner ADD CONSTRAINT vrn_uniq UNIQUE (vrn);
```

### Models Extended

1. **res.partner**
   - Adds `vrn` field
   - Overrides `vat` field label
   - Adds format validation
   - Adds unique constraints

2. **account.move**
   - Adds journal type validation
   - Auto-corrects purchase journal assignment
   - Handles multi-currency scenarios

### API Reference

**Field Definitions:**
```python
# res.partner
vat = fields.Char(
    string='TIN (Taxpayer ID)',
    tracking=True
)

vrn = fields.Char(
    string='VRN (VAT Registration Number)',
    copy=False,
    tracking=True
)
```

**Validation Methods:**
```python
@api.constrains('vat')
def _check_tin_format(self):
    # Validates 9-digit TIN format

@api.constrains('vrn')
def _check_vrn_format(self):
    # Validates 40-XXXXXXX-X VRN format
```

## Migration from partner_vat_number

If you previously used the `partner_vat_number` module:

1. **Check Data**
   ```sql
   SELECT id, name, vat, vrn FROM res_partner WHERE vrn IS NOT NULL;
   ```

2. **Backup Database**
   ```bash
   pg_dump odoo > backup_before_migration.sql
   ```

3. **Uninstall Old Module**
   - Apps → Search "partner_vat_number"
   - Click Uninstall
   - This will mark it as uninstalled but keep data

4. **Install New Module**
   - Apps → Search "VPA Tanzania"
   - Click Install
   - Data will be preserved

5. **Verify**
   - Open Contacts → Check TIN/VRN fields
   - All data should be intact

## Support

### Getting Help

- **Email:** support@vpasoftware.com
- **Website:** https://www.vpasoftware.com
- **Documentation:** [Full Docs](https://docs.vpasoftware.com/tanzania)

### Feature Requests

We welcome feature requests! Common requests:
- Chart of Accounts for Tanzania
- TRA tax report formats
- Shilling (TZS) currency formatting
- Bank account validation
- Phone number validation (+255 format)

Email us at: support@vpasoftware.com

## License

**Odoo Proprietary License v1.0 (OPL-1)**

This module is proprietary software. Key terms:
- ✅ Use with valid Odoo Enterprise subscription
- ✅ Modify for your own use
- ❌ Cannot redistribute or resell
- ❌ Cannot publish on other app stores
- ❌ Source code remains proprietary

See LICENSE file for complete terms.

## Credits

**Author:** VPA Software Limited
**Copyright:** © 2025 VPA Software Limited
**License:** OPL-1
**Version:** 19.0.1.0.0

---

🇹🇿 **Made for Tanzania** | 🏢 **TRA Compliant** | 🔒 **Enterprise Ready**
