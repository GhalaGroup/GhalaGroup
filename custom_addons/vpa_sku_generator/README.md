# Product Sequence Configuration

**Professional SKU Management for Odoo 19**

Version: 19.0.1.0.0 (v1.0)
License: OPL-1 (Odoo Proprietary License)
Copyright © 2025 VPA Software Limited
Price: $79.99 USD

## Overview

Product Sequence Configuration is a comprehensive SKU (Internal Reference) management solution that automates the generation of product codes based on your category hierarchy. Perfect for businesses that need consistent, professional product identification across their entire inventory.

## Key Features

- ✅ **Auto-Generate SKUs** - Automatically create SKUs based on category hierarchy (e.g., FUR/TBL/00001)
- ✅ **Product Variant Support** - Sequential suffixes for variants (00001-001, 00001-002)
- ✅ **SKU Locking** - Protect specific products from automatic regeneration
- ✅ **Gap Filling** - Recycle deleted product SKUs to eliminate sequence gaps
- ✅ **Bulk Regeneration** - Preview and regenerate SKUs for all products or by category
- ✅ **Validation Rules** - Require category, require SKU, block manual entry options
- ✅ **4-Tab Settings Page** - Organized configuration interface
- ✅ **Multi-Company Support** - Separate sequences per company
- ✅ **Comprehensive Statistics** - Track SKU usage and locks

## Installation

1. Download and install the module from Odoo Apps
2. Go to Apps menu and click "Update Apps List"
3. Search for "Product Sequence Configuration"
4. Click Install

## Quick Start

### 1. Set Up Category Short Codes

Navigate to **Inventory → Configuration → Product Categories**

Assign short codes to your categories:
- Furniture → FUR
- Tables → TBL
- Chairs → CHR

### 2. Configure Settings

Go to **Inventory → Configuration → Product Sequence Configuration**

Choose your preferences:
- Enable/disable auto-generation
- Set validation rules
- Enable SKU recycling

### 3. Create Products

Create a new product and select a category. The SKU will be automatically generated!

Example:
- Category: Furniture → Tables
- Generated SKU: **FUR/TBL/00001**

## SKU Format Examples

### Simple Products
```
Category: Furniture → Tables → Dining
Short Codes: FUR → TBL → DIN
Generated SKU: FUR/TBL/DIN/00001
```

### Products with Variants
```
Template SKU: FUR/TBL/00005
Variant 1 (Small): FUR/TBL/00005-001
Variant 2 (Medium): FUR/TBL/00005-002
Variant 3 (Large): FUR/TBL/00005-003
```

## Features in Detail

### Auto-Generation
- SKUs generate automatically when selecting a category
- Works on product creation, category change, and duplication
- Can be enabled/disabled in settings

### SKU Locking
- Lock checkbox on each product template
- Prevents automatic SKU changes
- Locks template and all variants
- Override protection during regeneration

### Recycle Pool
- Deleted product SKUs are saved for reuse
- Fills gaps in numbering sequences
- Configurable per company
- Prevents sequence gaps

### Regenerate Wizard
- Preview changes before applying
- Regenerate all products, by category, or selection
- Respect locks option
- Use recycle pool option
- Before/after comparison

### Validation Rules
- **Require Category:** Make category mandatory
- **Require SKU:** Make SKU mandatory
- **Block Manual Entry:** Prevent manual SKU editing

## Settings Page

Access via **Inventory → Configuration → Product Sequence Configuration**

### Tab 1: General Settings
- Auto-generation toggle
- Validation rules
- Statistics dashboard
- Quick actions (Regenerate, View Locked)

### Tab 2: Categories
- Manage category short codes
- View examples and hierarchy
- Category statistics

### Tab 3: Sequences
- View all sequences
- Multi-company management
- Sequence information

### Tab 4: Recycle Pool
- View recycled SKUs
- Enable/disable recycling
- Pool statistics

## Technical Details

### Models
- `product.template` - Extended with `sku_locked` field
- `product.product` - Variant SKU generation
- `product.category` - Short codes and statistics
- `product.sku.recycle.pool` - Recycled SKU tracking
- `regenerate.sku.wizard` - Bulk regeneration tool
- `res.config.settings` - Configuration options

### Dependencies
- `product` - Odoo Product module
- `stock` - Odoo Inventory module

### Security
- Stock User: Read access to recycle pool, full wizard access
- Stock Manager: Full access to all features
- System Admin: Access to settings

## Use Cases

Perfect for:
- Businesses with large product catalogs
- Companies with strict SKU formatting requirements
- Organizations needing category-based product codes
- Inventory systems requiring gap-free numbering
- Multi-company environments with separate sequences

## FAQ

**Q: What happens to variant SKUs when deleted?**
A: Variant SKUs (with suffixes like -001) are NOT recycled. Only template SKUs are added to the recycle pool.

**Q: Can I manually edit SKUs?**
A: Yes, unless you enable "Block Manual Entry" in settings. You can also lock specific products.

**Q: How do I fix gaps in my numbering?**
A: Enable "SKU Recycling" and the system will automatically reuse deleted SKUs.

**Q: Can I regenerate all SKUs at once?**
A: Yes, use the Regenerate SKUs wizard from settings. You can preview changes first.

**Q: Does this work with multi-company?**
A: Yes, each company has separate sequences and settings.

## Support

This is commercial software licensed under OPL-1.

**License:** OPL-1 (Odoo Proprietary License v1.0)
**Copyright:** © 2025 VPA Software Limited
**Version:** 19.0.1.0.0
**Compatible with:** Odoo 19.0

## License

This module is licensed under the Odoo Proprietary License v1.0 (OPL-1).

You may only use this software if you have purchased a valid license.
Redistribution or modification without authorization is prohibited.

See LICENSE file for full terms and conditions.

---

**Product Sequence Configuration** - Professional SKU Management
© 2025 VPA Software Limited - All Rights Reserved
