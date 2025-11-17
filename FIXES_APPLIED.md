# Odoo 19 Issues Fixed

## Issue 1: Broken Icons ✅ FIXED

### Problem
Icons and assets were not loading correctly due to multiple issues:
1. Websocket connection errors
2. Invalid module names with hyphens
3. Missing assets in database

### Root Cause
- Odoo 19 requires websocket/gevent port (8072) to be exposed
- Workers > 0 requires proper gevent configuration
- Module name `partner-vat-number` contains hyphens (invalid in Odoo 19)
- Error: `RuntimeError: Couldn't bind the websocket. Is the connection opened on the evented port (8072)?`
- Error: `FileNotFoundError: Invalid module name: partner-vat-number`

### Solutions Applied

1. **Added port 8072 mapping** in [docker-compose.yml](docker-compose.yml#L37)
   ```yaml
   ports:
     - "8071:8069"
     - "8072:8072"  # Added for websocket
   ```

2. **Added gevent_port configuration** in [config/odoo.conf](config/odoo.conf#L15)
   ```ini
   gevent_port = 8072
   ```

3. **Set workers to 0** in [config/odoo.conf](config/odoo.conf#L22) for development mode
   ```ini
   workers = 0  # Changed from 4
   ```
   Note: Workers > 0 requires production setup with proper gevent/threading

4. **Fixed invalid module name**
   - Renamed: `custom_addons/partner-vat-number` → `custom_addons/partner_vat_number`
   - Updated manifest name from `partner-vat-number` to `partner_vat_number`
   - Removed old module from database

5. **Cleaned incompatible modules from database**
   ```sql
   DELETE FROM ir_module_module WHERE name = 'partner-vat-number';
   UPDATE ir_module_module SET state = 'uninstalled'
   WHERE name IN ('direct_print', 'effective_date_change', 'garazd_product_label',
                  'garazd_product_label_print', 'garazd_product_label_pro',
                  'product_standard_price_tax_included');
   ```

6. **Force asset regeneration**
   ```sql
   DELETE FROM ir_attachment WHERE name LIKE 'web.assets_%';
   ```

### Verification ✅
- Websocket connects successfully (HTTP 101 response)
- Assets generating correctly:
  - `web.assets_web.min.css` ✅
  - `web.assets_frontend.min.css` ✅
  - `web.assets_web_print.min.css` ✅
- Font files loading: `fontawesome-webfont.woff2`, `odoo_ui_icons.woff2` ✅
- Icons and images loading properly ✅

### How to Clear Browser Cache
If icons still appear broken in your browser:
- **Chrome/Edge**: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- **Firefox**: `Ctrl+Shift+Delete` → Clear cache
- Or open in incognito/private window

---

## Issue 2: Invalid Account Statements ⚠️ IDENTIFIED

### Problem Analysis
Found data integrity issues in bank statements:

1. **22 Incomplete Statements** out of 3,807 total
2. **Balance Mismatches** due to floating-point precision
3. **1 Statement Missing Date** (ID: 4580)

### Examples of Issues Found

| ID   | Name                       | Balance Start | Balance End Real | Balance End | Date       | Issue                    |
|------|----------------------------|---------------|------------------|-------------|------------|--------------------------|
| 4580 | STANT Statement 2024-01-08 | 470996.21     | 466276.21        | 470996.21   | NULL       | Missing date + mismatch  |
| 4653 | CRDBT Statement 2024-01-05 | 9079498.88    | 8184978.10...    | 8184978.10  | 2024-01-05 | Floating point precision |
| 4654 | CRDBT Statement 2024-01-11 | 8184978.10... | 8109378.10...    | 8109378.10  | 2024-01-11 | Floating point precision |

### Recommended Actions

1. **Fix Statement #4580 (Missing Date)**
   ```sql
   UPDATE account_bank_statement
   SET date = '2024-01-08'
   WHERE id = 4580;
   ```

2. **Review Incomplete Statements** (22 statements)
   - Check these in Odoo UI: Accounting → Bank → Statements
   - Filter by incomplete statements
   - Complete reconciliation or mark as complete

3. **Fix Floating Point Issues** (if causing problems)
   ```sql
   UPDATE account_bank_statement
   SET balance_end_real = ROUND(balance_end_real::numeric, 2);
   ```

### How to Apply Fixes

Run the fix script:
```bash
docker-compose exec -T db psql -U odoo -d odoo << 'EOF'
-- Fix missing date
UPDATE account_bank_statement
SET date = '2024-01-08'
WHERE id = 4580 AND date IS NULL;

-- Round floating point balances
UPDATE account_bank_statement
SET balance_end_real = ROUND(balance_end_real::numeric, 2),
    balance_start = ROUND(balance_start::numeric, 2),
    balance_end = ROUND(balance_end::numeric, 2);

-- Report results
SELECT COUNT(*) as fixed_statements FROM account_bank_statement;
EOF
```

---

## Quick Commands

### Restart Services
```bash
docker-compose restart odoo
```

### View Logs
```bash
docker-compose logs -f odoo
```

### Access PostgreSQL
```bash
docker-compose exec db psql -U odoo -d odoo
```

### Check Service Status
```bash
docker-compose ps
```

---

## Next Steps

1. ✅ Icons should now load correctly (restart browser/clear cache)
2. ⚠️  Review the 22 incomplete bank statements in Odoo UI
3. ⚠️  Optionally run the SQL fixes for statement data issues
4. 📊 Monitor logs for any other errors

---

**Updated:** 2025-11-15
