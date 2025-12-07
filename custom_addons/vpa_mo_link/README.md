# VPA - Manufacturing Order Link

![License: OPL-1](https://img.shields.io/badge/license-OPL--1-blue)
![Version](https://img.shields.io/badge/version-1.0-brightgreen)
![Odoo](https://img.shields.io/badge/odoo-19.0-purple)

## Overview

**VPA - Manufacturing Order Link** is a powerful Odoo module that extends the standard manufacturing integration to provide flexible Manufacturing Order (MO) management workflows. Perfect for businesses that need both automatic and manual MO creation, with full control over the manufacturing process.

## Key Features

### 🎯 Draft MO Creation
- **All auto-created MOs stay in DRAFT** - Never auto-confirmed, giving you full review control
- Review quantities, dates, and components before confirming production
- Perfect for quality control and planning workflows

### 🔧 No-BOM Support
- **Create MOs even without Bill of Materials (BOM)**
- System creates basic MO structure when BOM is missing
- User can manually set BOM after MO creation
- Warning notifications when MO created without BOM

### 🔗 Manual MO Linking
- **Link MOs created BEFORE Sales Orders**
- Supports pre-production scenarios
- Two linking methods:
  1. Automatic: Fill Source field in MO with SO number
  2. Manual: Use "MO - Link" action button

### 📊 Unified Smart Button
- Single "Manufacturing" button shows ALL linked MOs
- Displays both automatically and manually linked orders
- Clean, unified view of production status
- Click to view detailed MO list or single MO form

### ⚙️ Production Route
- **"Production" route automatically created on installation**
- Product-selectable route for manufacturing items
- Works alongside standard "Manufacture" route
- Compatible with multi-warehouse setups

## Workflows Supported

### Workflow 1: Standard Automatic Creation
```
Product Setup → Assign "Production" Route
↓
Create Sales Order → Add product → Confirm SO
↓
MO Created Automatically (DRAFT state)
↓
Review MO → Set/Verify BOM → Confirm MO
↓
Start Production
```

### Workflow 2: No-BOM Product
```
Product with Production Route (No BOM)
↓
Confirm Sales Order
↓
MO Created in DRAFT (No BOM assigned)
↓
User Sets BOM Manually → Confirm MO
↓
Start Production
```

### Workflow 3: Pre-Production (Manual Linking)
```
Create MO First → Set Source = "S01234"
↓
Create Sales Order S01234
↓
MO Automatically Appears in SO Smart Button
↓
Continue with production as normal
```

### Workflow 4: Link Action
```
Create MO (Source empty)
↓
Create Sales Order
↓
Open SO → Action Menu → "MO - Link"
↓
System finds MOs with matching Source
↓
Creates link → MO appears in smart button
```

## Installation

### Requirements
- Odoo 19.0 Enterprise Edition
- Modules: `sale_mrp`, `mrp`, `stock`

### Installation Steps

1. **Copy module to addons folder:**
   ```bash
   cp -r vpa_mo_link /path/to/odoo/addons/
   ```

2. **Restart Odoo:**
   ```bash
   sudo systemctl restart odoo
   ```

3. **Update Apps List:**
   - Go to Apps menu
   - Click "Update Apps List"

4. **Install Module:**
   - Search for "VPA - Manufacturing Order Link"
   - Click Install

5. **Verify Installation:**
   - Go to Sales → Create quotation
   - Check Action menu has "MO - Link" and "MO - Unlink"
   - Go to Inventory → Products → Routes
   - Verify "Production" route exists

## Configuration

### 1. Configure Products

**For products that should trigger MO creation:**

1. Go to **Inventory → Products → Products**
2. Open product
3. Go to **Inventory tab**
4. Under **Routes**, check **"Production"**
5. Optionally create a Bill of Materials (BOM)
6. Save

### 2. Configure Warehouses

Manufacturing must be enabled in warehouses:

1. Go to **Inventory → Configuration → Warehouses**
2. Open warehouse
3. Under **Manufacturing**, ensure settings are configured
4. Manufacturing Location should be set
5. Save

### 3. Optional: Create BOMs

1. Go to **Manufacturing → Products → Bills of Materials**
2. Click **Create**
3. Select product
4. Add components
5. Set manufacturing type (e.g., Manufacture this product)
6. Save

## Usage Guide

### Creating Automatic MOs

1. **Setup Product:**
   - Assign "Production" route to product
   - (Optional) Create BOM

2. **Create Sales Order:**
   - Go to Sales → Create quotation
   - Add product with Production route
   - Set quantity
   - Save quotation

3. **Confirm SO:**
   - Click "Confirm" button
   - MO created automatically in DRAFT state

4. **Review MO:**
   - Click "Manufacturing" smart button on SO
   - Review MO details
   - If no BOM: Set BOM manually
   - Verify quantities and dates

5. **Confirm MO:**
   - Click "Confirm" on MO
   - Start production

### Manual Linking (Pre-Created MOs)

**Method 1: Using Source Field**

1. **Create MO:**
   - Go to Manufacturing → Create
   - Fill in product, quantity
   - In **Miscellaneous tab**, set **Source** = future SO number (e.g., "S01234")
   - Save as DRAFT

2. **Create Sales Order:**
   - Create SO with number matching MO Source
   - MO automatically appears in smart button

**Method 2: Using MO - Link Action**

1. **Create MO:**
   - Create MO (leave Source empty)
   - Save as DRAFT

2. **Create Sales Order:**
   - Create and save SO

3. **Link MO to SO:**
   - Open SO
   - Click **Action → MO - Link**
   - System searches for MOs with matching Source
   - Creates link
   - MO appears in smart button

### Unlinking MOs

To remove link between SO and MO (without deleting MO):

1. Open Sales Order
2. Click **Action → MO - Unlink**
3. MO removed from smart button
4. MO still exists but no longer linked to SO

## Technical Details

### Fields Added

**Sale Order (`sale.order`):**
- Extends `mrp_production_ids` (computed field from sale_mrp)
- Extends `mrp_production_count` (computed field from sale_mrp)
- Adds `procurement_group_id` compatibility property

### Methods Overridden

**Stock Rule (`stock.rule`):**
```python
_should_auto_confirm_procurement_mo(p)
```
- Returns `False` to keep all MOs in DRAFT

```python
_prepare_mo_vals(...)
```
- Handles missing BOM case
- Creates basic MO structure when BOM not found

**Sale Order (`sale.order`):**
```python
@api.depends('stock_reference_ids.production_ids', 'name')
def _compute_mrp_production_ids(self):
```
- Extends parent method
- Includes MOs where `origin` field matches SO name

### Server Actions

**MO - Link (`action_mo_link`):**
- Searches for MOs with `origin = SO.name`
- Triggers recomputation of `mrp_production_ids`
- Adds chatter messages for audit trail

**MO - Unlink (`action_mo_unlink`):**
- Finds MOs linked via origin
- Clears `origin` field
- Triggers recomputation
- Logs unlinking in chatter

### Routes and Rules

**Production Route:**
- ID: `vpa_mo_link.route_production`
- Type: Product-selectable
- Action: Triggers `manufacture` action on stock rules
- Created automatically on module installation

## Compatibility

### Odoo Versions
- ✅ Odoo 19.0 Enterprise

### Modules
- ✅ Compatible with `sale_mrp`
- ✅ Compatible with `mrp`
- ✅ Compatible with `stock`
- ✅ Compatible with `sale_stock`
- ✅ Works with VPA Document Layout

### Multi-Company
- ✅ Fully compatible
- Routes can be company-specific

### Multi-Warehouse
- ✅ Fully compatible
- Rules created per warehouse

## Troubleshooting

### MO Not Created After Confirming SO

**Check:**
1. Product has "Production" route selected
2. Warehouse has manufacturing enabled
3. Check Odoo logs for errors

**Solution:**
- Verify route configuration
- Ensure MRP module installed
- Check user permissions

### Icon Not Showing in Apps

**Check:**
1. File exists at `static/description/icon.png` (lowercase)
2. File is PNG format
3. Browser cache cleared

**Solution:**
```bash
# Restart Odoo
sudo systemctl restart odoo

# Clear browser cache
Ctrl+F5 (or Cmd+Shift+R on Mac)
```

### MO - Link Action Not Found

**Check:**
1. Module installed correctly
2. User has Manufacturing rights

**Solution:**
```bash
# Upgrade module
odoo -u vpa_mo_link -d your_database --stop-after-init
```

### Smart Button Not Showing MOs

**Check:**
1. MO `origin` field matches SO `name`
2. MO not in cancelled state

**Solution:**
- Manually trigger recomputation:
  - Open SO
  - Click "MO - Link" action
  - Should refresh the link

## Support

### Documentation
- README: `/custom_addons/vpa_mo_link/README.md`
- Inline code documentation in Python files

### Contact
- **Developer:** Your Company
- **Website:** https://www.yourcompany.com
- **Email:** support@yourcompany.com

### Bug Reports
Please report bugs with:
- Odoo version
- Module version
- Steps to reproduce
- Error logs (if applicable)

## Changelog

### Version 1.0 (2024)
- Initial release
- Draft MO creation
- No-BOM support
- Manual MO linking
- Production route creation
- MO - Link/Unlink actions
- Unified smart button
- Full compatibility with sale_mrp

## License

**Odoo Proprietary License v1.0 (OPL-1)**

This software and associated files (the "Software") may only be used (executed, modified, executed after modifications) with a valid Odoo Enterprise subscription for the correct number of users.

With a valid Partnership Agreement with Odoo S.A., the above permissions are also granted without limitation in time for partners and provided the software is used within the scope of the partnership agreement.

You may develop Odoo modules based on the Software and distribute them under the license of your choice, provided that it is compatible with the terms of the OPL-1.

You may use Odoo modules published under any license along with the Software.

It is forbidden to publish, distribute, sublicense, or sell copies of the Software or modified copies of the Software.

The above copyright notice and this permission notice must be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Credits

### Contributors
- Your Company Development Team

### Maintainer
This module is maintained by Your Company.

---

**© 2024 Your Company. All rights reserved.**
