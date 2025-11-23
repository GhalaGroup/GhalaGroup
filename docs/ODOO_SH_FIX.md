# Odoo.sh Database Fix Instructions

## Problem
Odoo.sh database has incorrect module names that don't match the actual folder names.

## Solution
Run these SQL commands in Odoo.sh Shell to fix the database:

### Step 1: Access Odoo.sh Shell
1. Go to your Odoo.sh Beta environment
2. Click on "Shell" or "Database" tab
3. Access the Python shell

### Step 2: Run This Python Code

```python
# Fix module names in database
env.cr.execute("""
    UPDATE ir_module_module
    SET name = 'partner_vat_number'
    WHERE name = 'partner-vat-number'
""")

env.cr.execute("""
    UPDATE ir_model_data
    SET module = 'partner_vat_number'
    WHERE module = 'partner-vat-number'
""")

env.cr.execute("""
    UPDATE ir_module_module
    SET name = 'vpa_sku_generator'
    WHERE name = 'product_sequence'
""")

env.cr.execute("""
    UPDATE ir_model_data
    SET module = 'vpa_sku_generator'
    WHERE module = 'product_sequence'
""")

# Commit changes
env.cr.commit()

print("✅ Module names fixed!")
```

### Step 3: Update Apps List
After running the SQL fix, go to Apps → Update Apps List

## What This Fixes

1. ✅ `partner-vat-number` → `partner_vat_number` (Odoo doesn't allow dashes in module names)
2. ✅ `product_sequence` → `vpa_sku_generator` (module was renamed)
3. ✅ `direct_print` version updated to 19.0 (already in code)
4. ✅ `product_standard_price_tax_included` version updated to 19.0 (already in code)

## After Fix
All modules should install without errors on Odoo.sh Beta.
