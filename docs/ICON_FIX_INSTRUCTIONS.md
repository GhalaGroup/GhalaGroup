# App Icons Not Showing - Complete Fix

## Current Status

The app icons in your Odoo 19 instance are showing as generic placeholder boxes. I've verified:

✅ All icon files exist and are accessible
✅ Websocket is working properly
✅ Assets are being generated correctly
✅ Menu web_icon database fields are properly configured
✅ Icon URLs return HTTP 200 (icons are accessible)

## Root Cause

The icons showing as placeholders is likely due to **browser caching of old assets** from before the websocket fix was applied.

## Solution Steps

### Step 1: Force Complete Browser Cache Clear

1. **Close ALL browser windows** with Odoo open
2. **Clear browser cache completely**:

   **Chrome/Edge:**
   - Press `Cmd+Shift+Delete` (Mac) or `Ctrl+Shift+Delete` (Windows/Linux)
   - Select "All time" as time range
   - Check "Cached images and files"
   - Click "Clear data"

   **Firefox:**
   - Press `Cmd+Shift+Delete` (Mac) or `Ctrl+Shift+Delete` (Windows/Linux)
   - Select "Everything" as time range
   - Check "Cache"
   - Click "Clear Now"

   **Safari:**
   - Safari menu → Settings → Privacy → Manage Website Data
   - Remove localhost:8071
   - Or: Develop menu → Empty Caches

3. **Open in Incognito/Private mode** as a test:
   - Chrome: `Cmd+Shift+N` (Mac) or `Ctrl+Shift+N` (Windows)
   - Firefox: `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows)
   - Safari: `Cmd+Shift+N`

4. **Navigate to**: http://localhost:8071
5. **Hard refresh**: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows/Linux)

### Step 2: Verify Icon Access

Test that icons are accessible by visiting these URLs directly:

- http://localhost:8071/spreadsheet_dashboard/static/description/icon.png
- http://localhost:8071/point_of_sale/static/description/icon.png
- http://localhost:8071/accountant/static/description/icon.png
- http://localhost:8071/mass_mailing/static/description/icon.png
- http://localhost:8071/purchase/static/description/icon.png
- http://localhost:8071/stock/static/description/icon.png

All should show actual app icons (not 404 or errors).

### Step 3: If Icons Still Don't Show

If after clearing cache the icons still show as placeholders, run this SQL fix:

```bash
docker-compose exec -T db psql -U odoo -d odoo << 'EOF'
-- Clear all menu web_icon_data cache
UPDATE ir_ui_menu SET web_icon_data = NULL WHERE parent_id IS NULL;

-- Verify the web_icon paths are correct
SELECT id, name->>'en_US' as app_name, web_icon
FROM ir_ui_menu
WHERE parent_id IS NULL
ORDER BY sequence;
EOF
```

Then restart Odoo:
```bash
docker-compose restart odoo
```

### Step 4: Nuclear Option - Full Asset Rebuild

If nothing else works, force complete asset regeneration:

```bash
# Stop Odoo
docker-compose stop odoo

# Clear all assets from database
docker-compose exec -T db psql -U odoo -d odoo << 'EOF'
DELETE FROM ir_attachment WHERE name LIKE '%assets%' OR name LIKE '%bundle%';
DELETE FROM ir_attachment WHERE res_model = 'ir.ui.view' AND name LIKE 'web.%';
EOF

# Start Odoo
docker-compose start odoo

# Wait 30 seconds for startup
sleep 30

# Access the site to trigger asset generation
curl -I http://localhost:8071/web
```

Then clear browser cache again and test.

## Verification

Icons should look like colorful app-specific icons, not generic gray placeholder boxes:

- **Dashboards**: Green/blue spreadsheet icon
- **Point of Sale**: Blue shopping cart/POS icon
- **Accounting**: Blue accounting/calculator icon
- **Email Marketing**: Purple/pink email icon
- **Purchase**: Blue purchase/cart icon
- **Inventory**: Blue/green inventory box icon

## Database Icon Configuration

Current menu icon configuration:

| App             | Menu ID | web_icon Format                                  |
|-----------------|---------|--------------------------------------------------|
| Dashboards      | 616     | spreadsheet_dashboard,static/description/icon.png |
| Point of Sale   | 277     | point_of_sale,static/description/icon.png         |
| Accounting      | 164     | accountant,static/description/icon.png            |
| Email Marketing | 354     | mass_mailing,static/description/icon.png          |
| Purchase        | 380     | purchase,static/description/icon.png              |
| Inventory       | 238     | stock,static/description/icon.png                 |

## Technical Details

- Icon format in Odoo 19: `module_name,static/description/icon.png`
- Icons are served via: `http://localhost:8071/{module}/static/description/icon.png`
- Fallback icon: `/web/static/img/default_icon_app.png` (the gray box you're seeing)
- Assets are cached in `ir_attachment` table with names like `web.assets_*`

## Still Not Working?

If icons still don't show after all these steps:

1. Check browser console (F12) for JavaScript errors
2. Check Network tab (F12) to see if icon requests are failing
3. Look for any CSP (Content Security Policy) errors
4. Share screenshot of browser console errors

---

**Last Updated**: 2025-11-15
