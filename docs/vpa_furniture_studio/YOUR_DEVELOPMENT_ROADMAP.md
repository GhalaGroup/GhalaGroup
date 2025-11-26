# 🚀 VPA Furniture Studio - Your Development Roadmap

## ✅ Your Priority: BASE → Configurator

---

## 🎯 **IMMEDIATE PRIORITY**

### **Step 1: vpa_furniture_studio (BASE)**
**Timeline:** Weeks 1-4 (1 month)
**Price:** $2,000
**Priority:** **P0 - MUST BUILD FIRST**

#### What to Build:
1. **Module Structure**
   - `__manifest__.py` with dependencies
   - Module icon (128×128 PNG)
   - Basic folder structure (models, views, security, data)

2. **Core Models** (`models/furniture_product.py`)
   ```python
   class FurnitureProduct(models.Model):
       _inherit = 'product.template'

       # Furniture Identification
       is_furniture = fields.Boolean('Is Furniture Product')
       furniture_type = fields.Selection([
           ('door', 'Door'),
           ('cabinet', 'Cabinet'),
           ('desk', 'Desk'),
           ('chair', 'Chair'),
           ('table', 'Table'),
           ('shelf', 'Shelf'),
           ('wardrobe', 'Wardrobe'),
           ('drawer', 'Drawer'),
       ], string='Furniture Type')

       # Dimensions
       furniture_height = fields.Float('Height (mm)', default=750.0)
       furniture_width = fields.Float('Width (mm)')
       furniture_depth = fields.Float('Depth (mm)')

       # Computed Fields
       area_m2 = fields.Float('Area (m²)', compute='_compute_area', store=True)
       volume_m3 = fields.Float('Volume (m³)', compute='_compute_volume', store=True)

       # Multi-Currency Fields
       currency_id = fields.Many2one('res.currency', related='company_id.currency_id')

       @api.depends('furniture_height', 'furniture_width')
       def _compute_area(self):
           for product in self:
               if product.furniture_height and product.furniture_width:
                   product.area_m2 = (product.furniture_height * product.furniture_width) / 1000000
               else:
                   product.area_m2 = 0.0

       @api.depends('furniture_height', 'furniture_width', 'furniture_depth')
       def _compute_volume(self):
           for product in self:
               if product.furniture_height and product.furniture_width and product.furniture_depth:
                   product.volume_m3 = (product.furniture_height * product.furniture_width * product.furniture_depth) / 1000000000
               else:
                   product.volume_m3 = 0.0
   ```

3. **Views** (`views/furniture_product_views.xml`)
   - Extend product form view with furniture fields
   - Add furniture-specific filters
   - Create furniture product tree view

4. **Security** (`security/ir.model.access.csv`)
   - Access rights for furniture models
   - User groups (Manager, User)

5. **Data** (`data/furniture_data.xml`)
   - Default product categories (Doors, Cabinets, Desks, etc.)
   - Default UOM for furniture (mm, m², m³)

6. **Configuration**
   - Settings page for currency rounding rules
   - Company-level furniture defaults

#### Success Criteria:
- ✅ Module installs without errors
- ✅ Can create furniture product with dimensions
- ✅ Area and volume calculate correctly
- ✅ Appears in Apps menu with icon
- ✅ All views load correctly

#### Testing Checklist:
- [ ] Create new furniture product
- [ ] Set dimensions (H: 750mm, W: 1200mm, D: 600mm)
- [ ] Verify area calculation: 0.9 m²
- [ ] Verify volume calculation: 0.54 m³
- [ ] Check currency field shows TZS/USD/EUR
- [ ] Test multi-company (if applicable)

---

### **Step 2: vpa_furniture_configurator**
**Timeline:** Weeks 5-12 (2 months)
**Price:** $6,000
**Priority:** **P1 - BUILD SECOND**
**Dependencies:** BASE module

#### What to Build:

#### Phase 2A: BOM Groups Foundation (Weeks 5-7)

1. **BOM Group Model** (`models/furniture_bom_group.py`)
   ```python
   class FurnitureBOMGroup(models.Model):
       _name = 'furniture.bom.group'
       _description = 'BOM Group for Dynamic Material Selection'

       name = fields.Char('Group Name', required=True)
       # Examples: "Veneer Materials", "Edge Banding", "Hardware - Hinges"

       category_id = fields.Many2one('product.category',
                                     'Material Category',
                                     required=True,
                                     help='Product category to pull materials from')

       filter_domain = fields.Char('Filter Domain',
           help="Additional filter (e.g., [('is_veneer', '=', True)])")

       product_ids = fields.Many2many('product.product',
           compute='_compute_available_products',
           string='Available Products')

       sequence = fields.Integer('Sequence', default=10)
       active = fields.Boolean('Active', default=True)

       @api.depends('category_id', 'filter_domain')
       def _compute_available_products(self):
           for group in self:
               domain = [('categ_id', 'child_of', group.category_id.id)]
               if group.filter_domain:
                   domain += safe_eval(group.filter_domain)
               group.product_ids = self.env['product.product'].search(domain)
   ```

2. **Product Categories Setup** (`data/product_categories.xml`)
   - Create default categories:
     - Materials > Veneers (Oak, Walnut, Mahogany, Cherry)
     - Materials > Edge Bands (PVC, ABS, Veneer)
     - Hardware > Hinges (Concealed, Overlay, Inset)
     - Hardware > Handles (Modern, Classic, Bar)
     - Materials > Boards (MDF, Plywood, Chipboard)
     - Finishes > Paint
     - Finishes > Stain

3. **BOM Groups Data** (`data/bom_groups.xml`)
   ```xml
   <record id="bom_group_veneer" model="furniture.bom.group">
       <field name="name">Veneer Materials</field>
       <field name="category_id" ref="category_veneers"/>
       <field name="sequence">10</field>
   </record>

   <record id="bom_group_edge_banding" model="furniture.bom.group">
       <field name="name">Edge Banding</field>
       <field name="category_id" ref="category_edge_bands"/>
       <field name="sequence">20</field>
   </record>

   <record id="bom_group_hinges" model="furniture.bom.group">
       <field name="name">Hardware - Hinges</field>
       <field name="category_id" ref="category_hinges"/>
       <field name="sequence">30</field>
   </record>
   ```

4. **Views for BOM Groups** (`views/bom_group_views.xml`)
   - Tree view listing all BOM groups
   - Form view to create/edit BOM groups
   - Show available products (computed field)
   - Menu item: Furniture > Configuration > BOM Groups

#### Phase 2B: Configuration Wizard (Weeks 8-10)

5. **Configuration Wizard Model** (`wizard/furniture_configuration_wizard.py`)
   ```python
   class FurnitureConfigurationWizard(models.TransientModel):
       _name = 'furniture.configuration.wizard'
       _description = 'Product Configuration Wizard'

       # Step 1: Base Product Selection
       product_template_id = fields.Many2one('product.template',
           'Base Product', required=True,
           domain="[('is_furniture', '=', True)]")

       # Step 2: Dimensions
       furniture_height = fields.Float('Height (mm)', required=True)
       furniture_width = fields.Float('Width (mm)', required=True)
       furniture_depth = fields.Float('Depth (mm)', required=True)

       # Step 3: Material Selections
       material_selection_ids = fields.One2many('furniture.material.selection',
           'wizard_id', 'Material Selections')

       # Step 4: Pricing
       unit_price = fields.Monetary('Unit Price',
           compute='_compute_price',
           currency_field='currency_id')
       quantity = fields.Float('Quantity', default=1.0)
       currency_id = fields.Many2one('res.currency',
           related='company_id.currency_id')

       # Validation
       constraint_errors = fields.Text('Errors',
           compute='_compute_constraints')
       is_valid = fields.Boolean('Valid',
           compute='_compute_constraints')

       @api.depends('material_selection_ids', 'furniture_height',
                    'furniture_width', 'furniture_depth')
       def _compute_price(self):
           for wizard in self:
               # Calculate material costs
               material_cost = sum(wizard.material_selection_ids.mapped('price'))

               # Calculate area-based cost
               area = (wizard.furniture_height * wizard.furniture_width) / 1000000
               labor_cost = area * 50  # TZS 50,000 per m²

               # Total
               wizard.unit_price = material_cost + labor_cost

       def action_add_to_order(self):
           """Add configured product to sales order"""
           self.ensure_one()
           if not self.is_valid:
               raise UserError(_("Configuration has errors"))

           # Create product variant or update existing
           variant = self._create_product_variant()

           # Add to current order
           order_id = self.env.context.get('active_id')
           if order_id:
               self.env['sale.order.line'].create({
                   'order_id': order_id,
                   'product_id': variant.id,
                   'product_uom_qty': self.quantity,
                   'price_unit': self.unit_price,
               })

           return {'type': 'ir.actions.act_window_close'}
   ```

6. **Material Selection Model** (`wizard/furniture_material_selection.py`)
   ```python
   class FurnitureMaterialSelection(models.TransientModel):
       _name = 'furniture.material.selection'
       _description = 'Material Selection Line'

       wizard_id = fields.Many2one('furniture.configuration.wizard', 'Wizard')
       bom_group_id = fields.Many2one('furniture.bom.group',
                                      'BOM Group',
                                      required=True)

       # Available options (computed from BOM Group)
       available_product_ids = fields.Many2many('product.product',
           compute='_compute_available_products',
           string='Available Materials')

       # User selection
       selected_product_id = fields.Many2one('product.product',
           'Selected Material',
           domain="[('id', 'in', available_product_ids)]")

       quantity = fields.Float('Quantity', default=1.0)
       uom_id = fields.Many2one('uom.uom',
                                related='selected_product_id.uom_id')
       price = fields.Monetary('Price',
                               compute='_compute_price',
                               currency_field='currency_id')
       currency_id = fields.Many2one('res.currency',
                                     related='wizard_id.currency_id')

       @api.depends('bom_group_id')
       def _compute_available_products(self):
           for line in self:
               line.available_product_ids = line.bom_group_id.product_ids

       @api.depends('selected_product_id', 'quantity')
       def _compute_price(self):
           for line in self:
               if line.selected_product_id:
                   line.price = line.selected_product_id.standard_price * line.quantity
               else:
                   line.price = 0.0
   ```

7. **Wizard Views** (`wizard/furniture_configuration_wizard_views.xml`)
   - Multi-step wizard form view
   - Step 1: Product selection dropdown
   - Step 2: Dimension input fields
   - Step 3: Material selection (one2many table with BOM groups)
   - Step 4: Pricing summary and quantity
   - Action buttons: Cancel, Add to Order

#### Phase 2C: Sales Order Integration (Weeks 11-12)

8. **Sales Order Extension** (`models/sale_order.py`)
   ```python
   class SaleOrder(models.Model):
       _inherit = 'sale.order'

       def action_configure_furniture(self):
           """Open furniture configuration wizard"""
           return {
               'name': 'Configure Furniture Product',
               'type': 'ir.actions.act_window',
               'res_model': 'furniture.configuration.wizard',
               'view_mode': 'form',
               'target': 'new',
               'context': {'active_id': self.id}
           }
   ```

9. **Sales Order View Extension** (`views/sale_order_views.xml`)
   - Add "Configure Furniture" button to sales order form
   - Show furniture specifications on order lines

10. **Menu Structure**
    ```
    Furniture (Main Menu)
    ├── Products
    │   └── Furniture Products
    ├── Sales
    │   └── Quotations / Orders
    ├── Configuration
    │   ├── BOM Groups
    │   ├── Product Categories
    │   └── Settings
    ```

#### Success Criteria:
- ✅ BOM Groups pull materials from inventory dynamically
- ✅ Configuration wizard opens from sales order
- ✅ Can select base product and set dimensions
- ✅ Material options populate from BOM Groups
- ✅ Price calculates automatically (materials + labor)
- ✅ Configured product adds to sales order
- ✅ Order line shows furniture specifications

#### Testing Checklist:
- [ ] Create BOM Group "Veneer Materials" linked to Veneers category
- [ ] Add 3 veneer products (Oak, Walnut, Mahogany) to inventory
- [ ] Verify BOM Group shows all 3 products automatically
- [ ] Create sales order
- [ ] Click "Configure Furniture" button
- [ ] Select base product: "Door Veneer"
- [ ] Set dimensions: H=2100mm, W=800mm, D=40mm
- [ ] Select Oak Veneer from materials
- [ ] Verify price calculates correctly
- [ ] Add to order
- [ ] Verify order line created with correct product and price

---

## 📋 **Development Checklist**

### Week 1-2: BASE Module Setup
- [ ] Create module folder structure
- [ ] Write `__manifest__.py`
- [ ] Create furniture_product model
- [ ] Add dimension fields (height, width, depth)
- [ ] Create computed fields (area, volume)
- [ ] Extend product form view
- [ ] Create security rules
- [ ] Add default product categories
- [ ] Test module installation
- [ ] Test product creation with dimensions

### Week 3-4: BASE Module Polish
- [ ] Add furniture type selection
- [ ] Create filters for furniture products
- [ ] Add currency handling
- [ ] Create settings page
- [ ] Write unit tests
- [ ] Create demo data
- [ ] Write user documentation
- [ ] Create module icon
- [ ] Final testing

### Week 5-7: BOM Groups (Configurator Phase 1)
- [ ] Create furniture.bom.group model
- [ ] Add category_id and filter_domain fields
- [ ] Create computed field for available products
- [ ] Create BOM Group views (tree, form)
- [ ] Add default product categories (Veneers, Edge Bands, Hardware)
- [ ] Create default BOM Groups data
- [ ] Add menu items
- [ ] Test dynamic product loading
- [ ] Test category filtering

### Week 8-10: Configuration Wizard (Configurator Phase 2)
- [ ] Create furniture.configuration.wizard model
- [ ] Add product selection, dimensions fields
- [ ] Create furniture.material.selection model
- [ ] Link material selections to BOM Groups
- [ ] Create wizard views (multi-step form)
- [ ] Implement price calculation logic
- [ ] Add validation rules
- [ ] Test wizard flow end-to-end

### Week 11-12: Sales Integration (Configurator Phase 3)
- [ ] Extend sale.order model
- [ ] Add "Configure Furniture" button
- [ ] Implement action_add_to_order method
- [ ] Create product variants from configuration
- [ ] Extend sale.order.line view
- [ ] Show furniture specifications on order lines
- [ ] Test full sales workflow
- [ ] Write user documentation
- [ ] Create demo video
- [ ] Final testing and bug fixes

---

## 🎯 **Milestones**

| Milestone | Completion Date | Deliverable |
|-----------|----------------|-------------|
| **M1: BASE Module Complete** | End of Week 4 | Working furniture product model with dimensions |
| **M2: BOM Groups Working** | End of Week 7 | Dynamic material selection from inventory |
| **M3: Configurator Wizard** | End of Week 10 | Working configuration wizard with pricing |
| **M4: Full Integration** | End of Week 12 | Complete sales-to-configured-product workflow |

---

## 💰 **Revenue After Completion**

After completing BASE + Configurator (3 months):
- Can sell **Starter Package** (5 modules) for $12,000
  - But only have 2 modules built (BASE + Configurator = $8,000)
  - **Gap:** Need Catalog, Reports, Product Catalogue for full Starter

**Recommendation:**
- Build BASE + Configurator first (3 months)
- Then choose one of these paths:
  1. **Path A:** Complete Starter Package (add Catalog, Reports, Catalogue) = 2 more months → Sell at $12K
  2. **Path B:** Add Manufacturing + Costing next → Can show full workflow → Sell custom packages
  3. **Path C:** Sell just BASE + Configurator for $8K to early adopters → Fund remaining development

---

## ❓ **After BASE + Configurator, What's Next?**

Tell me which modules to prioritize after Configurator:

**Option 1: Complete Starter Package** (sell $12K packages)
- [ ] Catalog
- [ ] Reports
- [ ] Product Catalogue

**Option 2: Core Production Workflow** (show full system)
- [ ] Manufacturing
- [ ] Costing
- [ ] Inventory Advanced

**Option 3: Quick Revenue - Universal Modules** (sell to any business)
- [ ] Label Designer
- [ ] Barcode/RFID
- [ ] Delivery Scheduling

---

## 📞 **Next Steps**

1. ✅ Start building BASE module (Week 1)
2. ✅ After BASE works, start Configurator (Week 5)
3. ❓ After Configurator complete (Week 12), what next?

Let me know your choice and I'll create detailed specs for the next modules!

---

**Last Updated:** November 23, 2025
**Your Current Focus:** BASE → Configurator → [You Decide Next]
