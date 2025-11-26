# 🏷️ Module 11: vpa_label_designer - Complete Development Specification

## 📋 Module Overview

**Module Name:** `vpa_label_designer`
**Price:** $4,000
**Type:** 🌐 **UNIVERSAL MODULE** (Can be sold to ANY business)
**Your Priority:** **#3** (After BASE and Configurator)
**Timeline:** 3-4 weeks
**Dependencies:** BASE module

---

## 🎯 What This Module Does

Professional **ZPL label designer** for **Zebra printers** with drag-and-drop visual designer. Create labels with:
- Barcodes (Code 128, Code 39, QR codes)
- Product information (name, SKU, price)
- Company logo
- Variable data fields
- Custom layouts

**Market:** Any business that needs labels - retail stores, warehouses, logistics, manufacturing, shipping companies.

---

## 🔧 **Technical Architecture**

### 1. **Label Template Model** (`models/label_template.py`)

```python
# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import base64

class LabelTemplate(models.Model):
    _name = 'label.template'
    _description = 'Label Template for ZPL Printing'
    _order = 'name'

    name = fields.Char('Template Name', required=True)
    # Example: "Product Label 4x6", "Shipping Label", "Inventory Barcode"

    active = fields.Boolean('Active', default=True)

    # Label Dimensions
    label_width = fields.Integer('Label Width (mm)', required=True, default=100)
    label_height = fields.Integer('Label Height (mm)', required=True, default=60)

    # Common sizes with selection helper
    label_size_preset = fields.Selection([
        ('custom', 'Custom Size'),
        ('4x6', '4" × 6" (102×152 mm) - Shipping'),
        ('4x3', '4" × 3" (102×76 mm) - Product'),
        ('2x1', '2" × 1" (51×25 mm) - Small Barcode'),
        ('3x2', '3" × 2" (76×51 mm) - Asset Tag'),
    ], string='Size Preset', default='custom')

    # Print Settings
    dpi = fields.Selection([
        ('203', '203 DPI'),
        ('300', '300 DPI'),
        ('600', '600 DPI'),
    ], string='Printer DPI', default='203', required=True)

    darkness = fields.Integer('Darkness (0-30)', default=15,
                              help='Print darkness, higher = darker')

    # Template Design
    element_ids = fields.One2many('label.element', 'template_id', 'Label Elements')

    # Generated ZPL Code
    zpl_code = fields.Text('ZPL Code', compute='_compute_zpl_code', store=True)

    # Preview
    preview_image = fields.Binary('Label Preview', compute='_compute_preview')

    # Usage Tracking
    print_count = fields.Integer('Times Printed', default=0, readonly=True)
    last_printed = fields.Datetime('Last Printed', readonly=True)

    # Company
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company)

    @api.onchange('label_size_preset')
    def _onchange_label_size_preset(self):
        """Auto-fill dimensions based on preset"""
        if self.label_size_preset == '4x6':
            self.label_width = 102
            self.label_height = 152
        elif self.label_size_preset == '4x3':
            self.label_width = 102
            self.label_height = 76
        elif self.label_size_preset == '2x1':
            self.label_width = 51
            self.label_height = 25
        elif self.label_size_preset == '3x2':
            self.label_width = 76
            self.label_height = 51

    @api.depends('element_ids', 'label_width', 'label_height', 'dpi', 'darkness')
    def _compute_zpl_code(self):
        """Generate ZPL code from template elements"""
        for template in self:
            zpl = []

            # ZPL Header
            zpl.append('^XA')  # Start of label
            zpl.append(f'^PW{template.label_width * 8}')  # Print width (dots)
            zpl.append(f'^LL{template.label_height * 8}')  # Label length (dots)
            zpl.append(f'^MD{template.darkness}')  # Media darkness

            # Add each element
            for element in template.element_ids.sorted('sequence'):
                element_zpl = element._generate_zpl()
                if element_zpl:
                    zpl.append(element_zpl)

            # ZPL Footer
            zpl.append('^XZ')  # End of label

            template.zpl_code = '\n'.join(zpl)

    @api.depends('zpl_code')
    def _compute_preview(self):
        """Generate preview image from ZPL (using Labelary API)"""
        for template in self:
            if template.zpl_code:
                # In production, call Labelary API or use local ZPL renderer
                # For now, placeholder
                template.preview_image = False
            else:
                template.preview_image = False

    def action_print_test(self):
        """Print a test label"""
        self.ensure_one()
        return self.env.ref('vpa_label_designer.action_print_label_wizard').read()[0]

    def action_duplicate(self):
        """Duplicate this template"""
        self.ensure_one()
        self.copy({'name': f"{self.name} (Copy)"})
```

---

### 2. **Label Element Model** (`models/label_element.py`)

```python
# -*- coding: utf-8 -*-
from odoo import models, fields, api

class LabelElement(models.Model):
    _name = 'label.element'
    _description = 'Label Element (Text, Barcode, Image, etc.)'
    _order = 'sequence, id'

    template_id = fields.Many2one('label.template', 'Label Template',
                                  required=True, ondelete='cascade')

    sequence = fields.Integer('Sequence', default=10)

    # Element Type
    element_type = fields.Selection([
        ('text', 'Text'),
        ('barcode', 'Barcode'),
        ('qrcode', 'QR Code'),
        ('image', 'Image/Logo'),
        ('line', 'Line'),
        ('box', 'Box/Rectangle'),
    ], string='Element Type', required=True, default='text')

    # Position (mm from top-left corner)
    pos_x = fields.Integer('X Position (mm)', default=5)
    pos_y = fields.Integer('Y Position (mm)', default=5)

    # ==================
    # TEXT ELEMENT
    # ==================
    text_content = fields.Char('Text Content')
    # Can use placeholders: {product_name}, {barcode}, {price}, etc.

    field_source = fields.Selection([
        ('static', 'Static Text'),
        ('product_name', 'Product Name'),
        ('product_barcode', 'Product Barcode'),
        ('product_default_code', 'Product SKU/Internal Ref'),
        ('product_price', 'Product Price'),
        ('product_weight', 'Product Weight'),
        ('company_name', 'Company Name'),
        ('custom', 'Custom Field'),
    ], string='Data Source', default='static')

    custom_field = fields.Char('Custom Field Name',
                               help='Technical field name (e.g., product_id.categ_id.name)')

    font_size = fields.Selection([
        ('20', 'Small (20pt)'),
        ('30', 'Medium (30pt)'),
        ('40', 'Large (40pt)'),
        ('50', 'Extra Large (50pt)'),
    ], string='Font Size', default='30')

    font_bold = fields.Boolean('Bold', default=False)

    # ==================
    # BARCODE ELEMENT
    # ==================
    barcode_type = fields.Selection([
        ('code128', 'Code 128'),
        ('code39', 'Code 39'),
        ('ean13', 'EAN-13'),
        ('upc', 'UPC'),
    ], string='Barcode Type', default='code128')

    barcode_height = fields.Integer('Barcode Height (mm)', default=15)
    barcode_show_text = fields.Boolean('Show Text Below Barcode', default=True)

    # ==================
    # QR CODE ELEMENT
    # ==================
    qr_size = fields.Selection([
        ('3', 'Small'),
        ('5', 'Medium'),
        ('7', 'Large'),
    ], string='QR Code Size', default='5')

    # ==================
    # IMAGE ELEMENT
    # ==================
    image_data = fields.Binary('Image Data')
    image_width = fields.Integer('Image Width (mm)', default=20)
    image_height = fields.Integer('Image Height (mm)', default=20)

    # ==================
    # LINE/BOX ELEMENT
    # ==================
    line_thickness = fields.Integer('Line Thickness (dots)', default=3)
    line_width = fields.Integer('Width (mm)', default=50)
    line_height = fields.Integer('Height (mm)', default=0)  # 0 = horizontal line

    def _generate_zpl(self):
        """Generate ZPL code for this element"""
        self.ensure_one()

        # Convert mm to dots (8 dots/mm for 203 DPI)
        x = self.pos_x * 8
        y = self.pos_y * 8

        if self.element_type == 'text':
            return self._generate_text_zpl(x, y)
        elif self.element_type == 'barcode':
            return self._generate_barcode_zpl(x, y)
        elif self.element_type == 'qrcode':
            return self._generate_qrcode_zpl(x, y)
        elif self.element_type == 'image':
            return self._generate_image_zpl(x, y)
        elif self.element_type == 'line':
            return self._generate_line_zpl(x, y)
        elif self.element_type == 'box':
            return self._generate_box_zpl(x, y)

        return ''

    def _generate_text_zpl(self, x, y):
        """Generate ZPL for text element"""
        text = self.text_content or ''

        # Get font
        font = 'A' if self.font_bold else '0'
        size = self.font_size or '30'

        zpl = f'^FO{x},{y}'  # Field Origin
        zpl += f'^A{font}N,{size},{size}'  # Font
        zpl += f'^FD{text}^FS'  # Field Data

        return zpl

    def _generate_barcode_zpl(self, x, y):
        """Generate ZPL for barcode element"""
        height = self.barcode_height * 8  # Convert mm to dots

        if self.barcode_type == 'code128':
            zpl = f'^FO{x},{y}'
            zpl += f'^BCN,{height},{"Y" if self.barcode_show_text else "N"}'
            zpl += f'^FD{{barcode}}^FS'  # Placeholder for actual barcode
        elif self.barcode_type == 'code39':
            zpl = f'^FO{x},{y}'
            zpl += f'^B3N,N,{height},{"Y" if self.barcode_show_text else "N"}'
            zpl += f'^FD{{barcode}}^FS'
        # Add other barcode types as needed

        return zpl

    def _generate_qrcode_zpl(self, x, y):
        """Generate ZPL for QR code element"""
        size = self.qr_size or '5'

        zpl = f'^FO{x},{y}'
        zpl += f'^BQN,2,{size}'  # QR Code
        zpl += f'^FD{{qrcode_data}}^FS'

        return zpl

    def _generate_image_zpl(self, x, y):
        """Generate ZPL for image element"""
        # Image conversion to ZPL is complex, requires GRF format
        # Simplified version - in production use proper image converter
        zpl = f'^FO{x},{y}'
        zpl += '^GFA,<bytes>,<total>,<rowbytes>,[image_data_hex]'
        zpl += '^FS'
        return zpl

    def _generate_line_zpl(self, x, y):
        """Generate ZPL for line element"""
        width = self.line_width * 8
        thickness = self.line_thickness

        zpl = f'^FO{x},{y}'
        zpl += f'^GB{width},{thickness},{thickness}^FS'  # Graphic Box
        return zpl

    def _generate_box_zpl(self, x, y):
        """Generate ZPL for box/rectangle element"""
        width = self.line_width * 8
        height = self.line_height * 8
        thickness = self.line_thickness

        zpl = f'^FO{x},{y}'
        zpl += f'^GB{width},{height},{thickness}^FS'
        return zpl
```

---

### 3. **Print Label Wizard** (`wizard/print_label_wizard.py`)

```python
# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import socket

class PrintLabelWizard(models.TransientModel):
    _name = 'print.label.wizard'
    _description = 'Print Label Wizard'

    template_id = fields.Many2one('label.template', 'Label Template', required=True)

    # Print Target
    print_target = fields.Selection([
        ('product', 'Product Label'),
        ('stock_picking', 'Shipping Label'),
        ('stock_quant', 'Inventory Label'),
        ('custom', 'Custom Data'),
    ], string='Print For', required=True, default='product')

    product_id = fields.Many2one('product.product', 'Product')
    picking_id = fields.Many2one('stock.picking', 'Picking/Shipment')
    quant_id = fields.Many2one('stock.quant', 'Stock Quant')

    # Custom data (for testing or manual printing)
    custom_data = fields.Text('Custom Data (JSON)',
                              help='{"barcode": "12345", "product_name": "Test"}')

    # Print Settings
    printer_id = fields.Many2one('label.printer', 'Printer')
    copies = fields.Integer('Number of Copies', default=1)

    # Preview
    preview_zpl = fields.Text('ZPL Code Preview', compute='_compute_preview_zpl')

    @api.depends('template_id', 'product_id', 'picking_id', 'custom_data')
    def _compute_preview_zpl(self):
        """Generate preview of ZPL with actual data"""
        for wizard in self:
            if wizard.template_id:
                zpl = wizard.template_id.zpl_code

                # Replace placeholders with actual data
                if wizard.product_id:
                    zpl = zpl.replace('{product_name}', wizard.product_id.name or '')
                    zpl = zpl.replace('{barcode}', wizard.product_id.barcode or '')
                    zpl = zpl.replace('{default_code}', wizard.product_id.default_code or '')
                    zpl = zpl.replace('{price}', str(wizard.product_id.list_price))

                wizard.preview_zpl = zpl
            else:
                wizard.preview_zpl = ''

    def action_print(self):
        """Send ZPL to printer"""
        self.ensure_one()

        if not self.printer_id:
            raise UserError("Please select a printer")

        zpl = self.preview_zpl

        # Send to printer
        for i in range(self.copies):
            self._send_to_printer(zpl)

        # Update template stats
        self.template_id.write({
            'print_count': self.template_id.print_count + self.copies,
            'last_printed': fields.Datetime.now(),
        })

        return {'type': 'ir.actions.act_window_close'}

    def _send_to_printer(self, zpl):
        """Send ZPL to network printer"""
        try:
            # Network printer (most common for Zebra)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.printer_id.ip_address, self.printer_id.port))
            sock.send(zpl.encode())
            sock.close()
        except Exception as e:
            raise UserError(f"Failed to print: {str(e)}")

    def action_download_zpl(self):
        """Download ZPL code as .zpl file"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/print.label.wizard/{self.id}/preview_zpl/label.zpl?download=true',
            'target': 'self',
        }
```

---

### 4. **Printer Configuration Model** (`models/label_printer.py`)

```python
# -*- coding: utf-8 -*-
from odoo import models, fields, api

class LabelPrinter(models.Model):
    _name = 'label.printer'
    _description = 'Label Printer Configuration'

    name = fields.Char('Printer Name', required=True)
    # Example: "Warehouse Zebra ZD620", "Shipping Label Printer"

    active = fields.Boolean('Active', default=True)

    # Connection Type
    connection_type = fields.Selection([
        ('network', 'Network (TCP/IP)'),
        ('usb', 'USB'),
        ('serial', 'Serial Port'),
    ], string='Connection Type', required=True, default='network')

    # Network Settings
    ip_address = fields.Char('IP Address')
    port = fields.Integer('Port', default=9100)

    # USB/Serial Settings
    device_path = fields.Char('Device Path',
                              help='e.g., /dev/usb/lp0 or COM3')

    # Printer Model
    printer_model = fields.Selection([
        ('zd420', 'Zebra ZD420'),
        ('zd620', 'Zebra ZD620'),
        ('zt410', 'Zebra ZT410'),
        ('zt420', 'Zebra ZT420'),
        ('generic', 'Generic ZPL Printer'),
    ], string='Printer Model', default='generic')

    # Printer Capabilities
    max_width = fields.Integer('Max Label Width (mm)', default=104)
    dpi = fields.Selection([
        ('203', '203 DPI'),
        ('300', '300 DPI'),
        ('600', '600 DPI'),
    ], string='Printer DPI', default='203')

    # Company
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company)

    def action_test_connection(self):
        """Test printer connection"""
        self.ensure_one()

        test_zpl = "^XA^FO50,50^A0N,50,50^FDTEST^FS^XZ"

        try:
            if self.connection_type == 'network':
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((self.ip_address, self.port))
                sock.send(test_zpl.encode())
                sock.close()
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Connection successful! Test label sent.',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError("USB/Serial testing not implemented yet")
        except Exception as e:
            raise UserError(f"Connection failed: {str(e)}")
```

---

## 📁 **File Structure**

```
vpa_label_designer/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── label_template.py          # Label template with elements
│   ├── label_element.py           # Text, barcode, QR, image elements
│   ├── label_printer.py           # Printer configuration
│   └── product_product.py         # Extend product with "Print Label" button
├── wizard/
│   ├── __init__.py
│   └── print_label_wizard.py      # Print wizard
├── views/
│   ├── label_template_views.xml   # Template form/tree views
│   ├── label_element_views.xml    # Element configuration views
│   ├── label_printer_views.xml    # Printer setup views
│   └── print_label_wizard_views.xml
├── data/
│   ├── label_template_demo.xml    # Demo templates
│   └── label_printer_demo.xml     # Demo printer config
├── security/
│   ├── ir.model.access.csv
│   └── label_security.xml
├── static/
│   ├── description/
│   │   ├── icon.png               # Module icon (128×128)
│   │   └── index.html             # Module description page
│   └── src/
│       ├── js/
│       │   └── label_designer_widget.js  # Drag-and-drop designer (future)
│       └── css/
│           └── label_designer.css
└── README.md
```

---

## 🎨 **Views to Create**

### 1. **Label Template Form View** (Designer Interface)

```xml
<record id="view_label_template_form" model="ir.ui.view">
    <field name="name">label.template.form</field>
    <field name="model">label.template</field>
    <field name="arch" type="xml">
        <form string="Label Template">
            <header>
                <button name="action_print_test" string="Print Test Label"
                        type="object" class="oe_highlight"/>
                <button name="action_duplicate" string="Duplicate Template"
                        type="object"/>
            </header>
            <sheet>
                <div class="oe_title">
                    <h1><field name="name" placeholder="e.g., Product Label 4x6"/></h1>
                </div>

                <group>
                    <group string="Label Settings">
                        <field name="label_size_preset"/>
                        <field name="label_width"/>
                        <field name="label_height"/>
                        <field name="dpi"/>
                        <field name="darkness"/>
                    </group>
                    <group string="Statistics">
                        <field name="print_count"/>
                        <field name="last_printed"/>
                        <field name="active"/>
                    </group>
                </group>

                <notebook>
                    <page string="Design Elements">
                        <field name="element_ids">
                            <tree editable="bottom">
                                <field name="sequence" widget="handle"/>
                                <field name="element_type"/>
                                <field name="pos_x"/>
                                <field name="pos_y"/>
                                <field name="text_content" attrs="{'invisible': [('element_type', '!=', 'text')]}"/>
                                <field name="field_source" attrs="{'invisible': [('element_type', '!=', 'text')]}"/>
                                <field name="barcode_type" attrs="{'invisible': [('element_type', '!=', 'barcode')]}"/>
                            </tree>
                        </field>
                    </page>

                    <page string="ZPL Code">
                        <field name="zpl_code" widget="ace" options="{'mode': 'text'}"/>
                    </page>

                    <page string="Preview">
                        <field name="preview_image" widget="image"/>
                    </page>
                </notebook>
            </sheet>
        </form>
    </field>
</record>
```

---

## ✅ **Success Criteria**

- [ ] Can create label template with custom dimensions
- [ ] Can add text elements with variable data sources
- [ ] Can add barcode (Code 128) with product barcode
- [ ] Can add QR code element
- [ ] Can add company logo image
- [ ] ZPL code generates correctly
- [ ] Can configure network printer (IP + port)
- [ ] Can test printer connection
- [ ] Can print label from product form ("Print Label" button)
- [ ] Can print from inventory (stock.quant)
- [ ] Can print from shipments (stock.picking)
- [ ] Multiple copies work correctly

---

## 🌐 **Universal Module - Market Potential**

This module can be sold to:
- ✅ **Retail stores** - Price tags, shelf labels
- ✅ **Warehouses** - Inventory labels, location tags
- ✅ **Logistics companies** - Shipping labels
- ✅ **Manufacturing** - Product labels, work order tags
- ✅ **Healthcare** - Patient wristbands, specimen labels
- ✅ **Food industry** - Nutrition labels, date labels
- ✅ **Asset management** - Asset tags, equipment labels

**Total Addressable Market:** 500,000+ businesses globally

---

## 📊 **Revenue Opportunity**

**Pricing:** $4,000 one-time OR $170/month OR $1,700/year

**Target:** Sell to 50 businesses in Year 1
- **Revenue:** 50 × $4,000 = **$200,000**
- OR (if subscriptions): 50 × $1,700/year = **$85,000/year recurring**

---

## ⏱️ **Development Timeline**

**Total:** 3-4 weeks

### Week 1: Core Models
- [ ] Create label_template model
- [ ] Create label_element model
- [ ] Basic ZPL generation (text + barcode)
- [ ] Template form view

### Week 2: Print Functionality
- [ ] Create label_printer model
- [ ] Create print_label_wizard
- [ ] Network printer connection
- [ ] Test printing workflow

### Week 3: Advanced Features
- [ ] QR code support
- [ ] Image/logo support
- [ ] Variable data sources (product fields)
- [ ] Integration with product/inventory/shipping

### Week 4: Polish & Testing
- [ ] Demo templates
- [ ] User documentation
- [ ] Testing with real Zebra printer
- [ ] Bug fixes

---

## 🚀 **After Label Designer**

Tell me what's next:
1. **Manufacturing** (core production workflow)
2. **Costing** (historical cost tracking)
3. **Inventory Advanced** (multi-box tracking)
4. **Reports** (dashboards)
5. **Product Catalogue** (series management)

Your current roadmap:
✅ BASE → ✅ Configurator → ✅ Label Designer → **[Your Choice Next]**

---

**Ready to start building?** Let me know if you need any clarification on the Label Designer specs!
