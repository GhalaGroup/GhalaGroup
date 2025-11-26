# VPA Furniture Studio - Module Dependencies Map

> **Technical dependency tree and installation guide**

[🏠 Back to Main](README.md) | [💰 Packages](PACKAGES.md) | [🎨 Icon Specs](MODULES_LIST.md) | [📘 Full Spec](MODULAR_ARCHITECTURE.html)

---

## 🌳 Complete Dependency Tree

```
vpa_furniture_studio (BASE) ← Foundation - Required by ALL modules
    │
    ├─── vpa_furniture_configurator
    │    ├─── vpa_furniture_bom_smart (Phase 2)
    │    └─── vpa_furniture_portal (Phase 4)
    │
    ├─── vpa_furniture_catalog
    │    └─── (standalone, no dependents)
    │
    ├─── vpa_furniture_reports
    │    └─── (standalone, no dependents)
    │
    ├─── vpa_furniture_costing
    │    └─── vpa_furniture_analytics (Phase 3)
    │
    ├─── vpa_furniture_manufacturing
    │    ├─── vpa_furniture_shopfloor
    │    ├─── vpa_furniture_nesting (Phase 3)
    │    └─── vpa_furniture_analytics (Phase 3)
    │
    ├─── vpa_inventory_advanced
    │    ├─── vpa_inventory_barcode
    │    └─── vpa_label_designer
    │
    ├─── vpa_product_catalogue
    │    └─── (standalone, no dependents)
    │
    ├─── vpa_quality_control
    │    └─── (standalone, no dependents)
    │
    └─── vpa_delivery_scheduling
         └─── (standalone, no dependents)
```

---

## 📋 Installation Order by Phase

### **Phase 1: Foundation (Months 1-6)**

**Install in this order:**

1. **vpa_furniture_studio (BASE)** - [Module Details](modules/MODULE_01_BASE.md)
   - Dependencies: Odoo core modules only
   - Install first - required by everything

2. **vpa_furniture_configurator** - [Module Details](modules/MODULE_02_CONFIGURATOR.md)
   - Dependencies: BASE
   - Install after BASE

3. **vpa_furniture_reports** - [Module Details](modules/MODULE_05_REPORTS.md)
   - Dependencies: BASE
   - Can install anytime after BASE

4. **vpa_furniture_catalog** - [Module Details](modules/MODULE_03_CATALOG.md)
   - Dependencies: BASE, REPORTS (optional)
   - Install after BASE

5. **vpa_furniture_manufacturing** - [Module Details](modules/MODULE_06_MANUFACTURING.md)
   - Dependencies: BASE, CONFIGURATOR (optional)
   - Install after BASE

6. **vpa_furniture_costing** - [Module Details](modules/MODULE_04_COSTING.md)
   - Dependencies: BASE, MANUFACTURING
   - Install after MANUFACTURING

7. **vpa_product_catalogue** - [Module Details](modules/MODULE_17_PRODUCT_CATALOGUE.md)
   - Dependencies: BASE
   - Can install anytime after BASE

8. **vpa_label_designer** - [Module Details](modules/MODULE_11_LABEL_DESIGNER.md)
   - Dependencies: BASE (universal module)
   - Can install anytime after BASE

9. **vpa_inventory_advanced** - [Module Details](modules/MODULE_09_INVENTORY_ADVANCED.md)
   - Dependencies: BASE
   - Install before BARCODE

---

### **Phase 2: Advanced Features (Months 7-9)**

10. **vpa_inventory_barcode** - [Module Details](modules/MODULE_10_INVENTORY_BARCODE.md)
    - Dependencies: BASE, INVENTORY_ADVANCED
    - Install after INVENTORY_ADVANCED

11. **vpa_furniture_shopfloor** - [Module Details](modules/MODULE_12_SHOPFLOOR.md)
    - Dependencies: BASE, MANUFACTURING, BARCODE (optional), LABEL_DESIGNER (optional)
    - Install after MANUFACTURING

12. **vpa_furniture_bom_smart** - [Module Details](modules/MODULE_07_BOM_SMART.md)
    - Dependencies: BASE, CONFIGURATOR, MANUFACTURING
    - Install after CONFIGURATOR and MANUFACTURING

---

### **Phase 3: Enterprise Features (Months 10-13)**

13. **vpa_quality_control** - [Module Details](modules/MODULE_13_QUALITY_CONTROL.md)
    - Dependencies: BASE, MANUFACTURING (optional), BARCODE (optional)
    - Universal module, flexible installation

14. **vpa_furniture_analytics** - [Module Details](modules/MODULE_14_ANALYTICS.md)
    - Dependencies: BASE, COSTING, MANUFACTURING
    - Install after COSTING and MANUFACTURING

15. **vpa_furniture_nesting** - [Module Details](modules/MODULE_08_NESTING.md)
    - Dependencies: BASE, MANUFACTURING, BOM_SMART (optional)
    - Install after MANUFACTURING

16. **vpa_delivery_scheduling** - [Module Details](modules/MODULE_16_DELIVERY_SCHEDULING.md)
    - Dependencies: BASE, MANUFACTURING (optional), QUALITY (optional)
    - Flexible installation

---

### **Phase 4: Customer Portal (Future)**

17. **vpa_furniture_portal** - [Module Details](modules/MODULE_15_PORTAL.md)
    - Dependencies: BASE, CONFIGURATOR
    - Install after CONFIGURATOR

---

## 🔗 Odoo Core Module Dependencies

Each VPA module depends on these Odoo core modules:

| VPA Module | Odoo Dependencies |
|------------|-------------------|
| **vpa_furniture_studio** | `product`, `stock`, `uom` |
| **vpa_furniture_configurator** | `sale_management` |
| **vpa_furniture_catalog** | `sale_management`, `product` |
| **vpa_furniture_costing** | `mrp`, `account` |
| **vpa_furniture_reports** | `sale_management`, `web` |
| **vpa_furniture_manufacturing** | `mrp`, `sale_management` |
| **vpa_furniture_bom_smart** | `mrp` |
| **vpa_furniture_nesting** | `mrp`, `stock` |
| **vpa_inventory_advanced** | `stock`, `purchase` |
| **vpa_inventory_barcode** | `stock`, `stock_barcode` (Odoo Enterprise) |
| **vpa_label_designer** | `stock` |
| **vpa_furniture_shopfloor** | `mrp`, `quality_control` (optional) |
| **vpa_quality_control** | `mrp`, `stock` |
| **vpa_furniture_analytics** | `mrp`, `sale_management`, `stock` |
| **vpa_furniture_portal** | `portal`, `website`, `sale_management` |
| **vpa_delivery_scheduling** | `sale_management`, `stock`, `delivery` (if available) |
| **vpa_product_catalogue** | `product`, `stock`, `sale_management` |

---

## 📦 Package Installation Guides

### 🥉 **Starter Package Installation**

**Modules to Install (in order):**
1. vpa_furniture_studio (BASE)
2. vpa_furniture_configurator
3. vpa_furniture_reports
4. vpa_furniture_catalog
5. vpa_product_catalogue

**Estimated Installation Time:** 2-4 hours
**Configuration Time:** 1-2 days
**Training Time:** 2-3 days

---

### 🥈 **Professional Package Installation**

**Modules to Install (in order):**
1. All Starter modules (above)
2. vpa_furniture_manufacturing
3. vpa_furniture_costing
4. vpa_inventory_advanced

**Estimated Installation Time:** 4-6 hours
**Configuration Time:** 3-5 days
**Training Time:** 1 week

---

### 🥇 **Advanced Package Installation**

**Modules to Install (in order):**
1. All Professional modules (above)
2. vpa_label_designer
3. vpa_inventory_barcode
4. vpa_furniture_shopfloor
5. vpa_furniture_bom_smart

**Estimated Installation Time:** 6-8 hours
**Configuration Time:** 1-2 weeks
**Training Time:** 2 weeks

---

### 💎 **Enterprise Package Installation**

**Modules to Install (in order):**
1. All Advanced modules (above)
2. vpa_quality_control
3. vpa_furniture_analytics
4. vpa_furniture_nesting
5. vpa_delivery_scheduling

**Estimated Installation Time:** 8-12 hours
**Configuration Time:** 2-3 weeks
**Training Time:** 3-4 weeks

---

### 🌟 **Ultimate Package Installation**

**Modules to Install (in order):**
1. All Enterprise modules (above)
2. vpa_furniture_portal

**Estimated Installation Time:** 10-14 hours
**Configuration Time:** 3-4 weeks
**Training Time:** 4-5 weeks

---

## ⚠️ Important Notes

### **Installation Prerequisites**

Before installing any VPA Furniture Studio module:

✅ **Odoo Version:** 19.0 Enterprise
✅ **Database:** PostgreSQL 12 or higher
✅ **Python:** 3.10 or higher
✅ **Server:** Minimum 4GB RAM, 2 CPU cores
✅ **Storage:** Minimum 20GB free space
✅ **Network:** Stable internet connection

### **Module Conflicts**

These modules should NOT be installed together with VPA modules:

❌ Other furniture-specific modules
❌ Conflicting barcode scanning apps
❌ Third-party label printing apps (if using vpa_label_designer)

### **Database Backup**

⚠️ **CRITICAL:** Always backup your database before installing new modules!

```bash
# Backup command
pg_dump your_database_name > backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## 🔄 Upgrade Paths

### **From Starter to Professional**

**Add these modules:**
- vpa_furniture_manufacturing
- vpa_furniture_costing
- vpa_inventory_advanced

**Migration Steps:**
1. Backup database
2. Install vpa_furniture_manufacturing
3. Configure manufacturing routes
4. Install vpa_furniture_costing
5. Import historical cost data (if available)
6. Install vpa_inventory_advanced
7. Test multi-box scenarios

**Estimated Upgrade Time:** 2-3 days

---

### **From Professional to Advanced**

**Add these modules:**
- vpa_label_designer
- vpa_inventory_barcode
- vpa_furniture_shopfloor
- vpa_furniture_bom_smart

**Migration Steps:**
1. Backup database
2. Install vpa_label_designer
3. Design label templates
4. Install vpa_inventory_barcode
5. Setup mobile devices and scanners
6. Install vpa_furniture_shopfloor
7. Configure workstations and tablets
8. Install vpa_furniture_bom_smart
9. Migrate existing BOMs to smart BOMs

**Estimated Upgrade Time:** 1 week

---

### **From Advanced to Enterprise**

**Add these modules:**
- vpa_quality_control
- vpa_furniture_analytics
- vpa_furniture_nesting
- vpa_delivery_scheduling

**Migration Steps:**
1. Backup database
2. Install vpa_quality_control
3. Setup inspection workflows
4. Install vpa_furniture_analytics
5. Configure dashboards
6. Install vpa_furniture_nesting (if using CNC)
7. Configure cutting parameters
8. Install vpa_delivery_scheduling
9. Setup delivery routes and drivers

**Estimated Upgrade Time:** 1-2 weeks

---

## 🛠️ Technical Installation Commands

### **Using Odoo CLI**

```bash
# Install single module
odoo-bin -c odoo.conf -i vpa_furniture_studio -d your_database --stop-after-init

# Install multiple modules
odoo-bin -c odoo.conf -i vpa_furniture_studio,vpa_furniture_configurator -d your_database --stop-after-init

# Upgrade existing module
odoo-bin -c odoo.conf -u vpa_furniture_studio -d your_database --stop-after-init
```

### **Using Odoo UI**

1. Navigate to **Apps** menu
2. Update Apps List (remove "Apps" filter)
3. Search for "VPA Furniture Studio"
4. Click **Install** on desired modules
5. Wait for installation to complete
6. Configure module settings

---

## 📊 Module Relationship Matrix

| Module | Requires | Required By | Optional For |
|--------|----------|-------------|--------------|
| BASE | None | All | None |
| CONFIGURATOR | BASE | BOM_SMART, PORTAL | MANUFACTURING |
| CATALOG | BASE | None | REPORTS |
| COSTING | BASE, MANUFACTURING | ANALYTICS | None |
| REPORTS | BASE | None | CATALOG |
| MANUFACTURING | BASE | SHOPFLOOR, NESTING, ANALYTICS | CONFIGURATOR |
| BOM_SMART | BASE, CONFIGURATOR, MANUFACTURING | None | NESTING |
| NESTING | BASE, MANUFACTURING | None | BOM_SMART |
| INVENTORY_ADV | BASE | BARCODE | None |
| BARCODE | BASE, INVENTORY_ADV | None | SHOPFLOOR, QUALITY |
| LABEL_DESIGNER | BASE | None | SHOPFLOOR, BARCODE |
| SHOPFLOOR | BASE, MANUFACTURING | None | BARCODE, LABEL_DESIGNER |
| QUALITY | BASE | None | MANUFACTURING, BARCODE |
| ANALYTICS | BASE, COSTING, MANUFACTURING | None | None |
| PORTAL | BASE, CONFIGURATOR | None | None |
| DELIVERY | BASE | None | MANUFACTURING, QUALITY |
| PRODUCT_CATALOGUE | BASE | None | None |

---

## 🔍 Troubleshooting Common Issues

### **Issue: Module Not Appearing in Apps List**

**Solution:**
1. Update the apps list (Apps → Update Apps List)
2. Remove "Apps" filter from search
3. Check module is in correct addons path
4. Restart Odoo server

### **Issue: Dependency Error During Installation**

**Solution:**
1. Check all required modules are installed
2. Install dependencies first (see dependency tree)
3. Update all modules to latest version
4. Check Odoo logs for specific error

### **Issue: Module Installed but Not Working**

**Solution:**
1. Clear browser cache
2. Restart Odoo server
3. Check user has correct access rights
4. Review configuration settings
5. Check Odoo logs for errors

---

## 📞 Support

### Installation Support
- Email: support@vpa-furniture-studio.com
- Phone: +255 XXX XXX XXX
- Documentation: [Installation Guide](https://docs.vpa-furniture-studio.com/install)

### Technical Issues
- GitHub Issues: [Report Bug](https://github.com/vpa/furniture-studio/issues)
- Community Forum: [Ask Question](https://forum.vpa-furniture-studio.com)

---

## 🔗 Related Documentation

- **[🏠 Main Documentation](README.md)** - Overview and navigation
- **[💰 Packages & Pricing](PACKAGES.md)** - Pricing strategies
- **[🎨 Icon Design Specs](MODULES_LIST.md)** - For designers
- **[📘 Full Specification (HTML)](MODULAR_ARCHITECTURE.html)** - Technical details
- **[📂 Individual Modules](modules/)** - Detailed per-module specs

---

## 📄 Version Compatibility

| VPA Version | Odoo Version | Python | PostgreSQL |
|-------------|--------------|--------|------------|
| 1.0 | 19.0 | 3.10+ | 12+ |
| Future 1.1 | 19.0 | 3.10+ | 12+ |
| Future 2.0 | 20.0 | 3.11+ | 13+ |

---

**Ready to install? Follow the guide above for a smooth installation!** 🚀

© 2025 VPA Furniture Studio. All rights reserved.
