# VPA Document Layout - Complete Architecture Guide

## 📋 Table of Contents
1. [Module Overview](#module-overview)
2. [File Structure](#file-structure)
3. [Core Architecture](#core-architecture)
4. [Data Flow](#data-flow)
5. [Key Components](#key-components)
6. [PDF Generation System](#pdf-generation-system)
7. [Template System](#template-system)
8. [Integration Points](#integration-points)
9. [Troubleshooting](#troubleshooting)

---

## Module Overview

**Purpose**: Advanced PDF report customization for Odoo 19 with live preview, zero-margin PDF generation, and per-document template management.

**Key Features**:
- ✅ Per-document-type templates (Quotations, Invoices, POs, etc.)
- ✅ Live HTML preview with exact paper dimensions
- ✅ Zero-margin PDF generation using wkhtmltopdf
- ✅ Dynamic QWeb template generation
- ✅ Custom colors, logos, headers, footers
- ✅ Multiple table styles and layouts
- ✅ Paper size/orientation configuration (A4/Letter, Portrait/Landscape)

---

## File Structure

```
vpa_document_layout/
├── __init__.py                          # Module entry point
├── __manifest__.py                      # Module definition & dependencies
├── README.md                            # User documentation
│
├── models/                              # Python business logic
│   ├── __init__.py
│   ├── vpa_document_template.py        # ⭐ MAIN: Template model with QWeb generation
│   ├── vpa_document_config.py          # OLD: Legacy config model (still used)
│   ├── ir_actions_report.py            # ⭐ CRITICAL: PDF generation with zero margins
│   ├── res_company.py                  # Company integration
│   └── res_config_settings.py          # Settings integration
│
├── controllers/                         # HTTP controllers
│   ├── __init__.py
│   └── main.py                          # ⭐ Template preview endpoints
│
├── views/                               # XML templates & views
│   ├── vpa_menu_root.xml               # Main menu entry
│   ├── vpa_template_views.xml          # ⭐ Template form view
│   ├── vpa_config_views.xml            # Legacy config views
│   ├── report_templates.xml            # OLD: Static external layout
│   ├── template_preview.xml            # ⭐ Live preview templates
│   ├── template_preview_fullpage.xml   # ⭐ Full-page preview with paper margins
│   ├── sale_order_report_inherit.xml   # Document inheritance
│   ├── account_invoice_report_inherit.xml
│   └── res_config_settings_views.xml   # Settings integration
│
├── data/                                # Data files
│   ├── report_layout.xml               # Register VPA as report.layout option
│   └── default_templates.xml           # ⭐ Default template creation
│
├── security/
│   └── ir.model.access.csv             # Access rights
│
└── static/
    └── src/
        ├── scss/vpa_document_layout.scss  # Form view styling
        ├── js/vpa_preview_widget.js       # (Optional) Preview widget
        └── xml/vpa_preview_widget.xml     # (Optional) Widget template
```

---

## Core Architecture

### 🏗️ Dual-Model System

#### 1. **vpa.document.template** (NEW - Current Active System)
- **Purpose**: Per-document-type template management
- **Key**: Each template = one report action + dynamically generated QWeb views
- **Usage**: Create multiple templates for different document types (quotations, invoices, etc.)
- **Records**: Many templates per company

#### 2. **vpa.document.config** (OLD - Legacy System)
- **Purpose**: Company-wide configuration with live preview
- **Key**: One config per company
- **Usage**: Used as reference/fallback for global settings
- **Records**: One config per company

### 🔄 Template Lifecycle

```
1. CREATE Template Record
   ↓
2. _create_report_action()
   - Creates ir.actions.report with unique report_name
   - Creates/updates 'VPA A4' paperformat (zero margins)
   - Binds to model (sale.order, account.move, etc.)
   ↓
3. _create_qweb_template()
   - Generates MAIN report template: report_template_{id}
   - Generates EXTERNAL LAYOUT: external_layout_vpa_template_{id}
   - Generates INHERITANCE VIEW: to replace web.external_layout calls
   ↓
4. USER prints document
   ↓
5. Odoo calls report_template_{id}
   ↓
6. Document template calls external_layout_vpa_template_{id}
   ↓
7. Layout wraps content with header/footer
   ↓
8. ir_actions_report._render_qweb_pdf_prepare_streams()
   - Detects VPA template via report_ref check
   - Sets context: vpa_force_zero_margins=True
   ↓
9. ir_actions_report._build_wkhtmltopdf_args()
   - Removes all margin args
   - Adds --margin-top 0, --margin-bottom 0, etc.
   ↓
10. wkhtmltopdf generates PDF with ZERO margins
```

---

## Data Flow

### 📊 Template Creation Flow

```python
# User creates template via form view
vpa.document.template.create({
    'name': 'Modern Sales Quote',
    'document_type': 'quotation',
    'target_app': 'sale',
    'paper_size': 'a4',
    'paper_orientation': 'portrait',
    # ... styling fields
})
```

**Automatic Actions**:
1. **@api.model create()** called
2. Calls `_create_report_action()`:
   - Gets or creates "VPA A4" paperformat with margins = 0
   - Creates `ir.actions.report` with `report_name = 'vpa_document_layout.report_template_{id}'`
   - Binds to model (e.g., sale.order)
3. Calls `_create_qweb_template()`:
   - Builds arch_content dynamically with template settings
   - Creates 3 QWeb views:
     - `vpa_document_layout.report_template_{id}` - Main report
     - `vpa_document_layout.external_layout_vpa_template_{id}` - Layout wrapper
     - `sale.report_saleorder_document_inherit_{id}` - XPath to replace external_layout

### 🖨️ PDF Generation Flow

```
USER clicks Print → Quotation
   ↓
Odoo looks up ir.actions.report for sale.order
   ↓
Finds report_name: 'vpa_document_layout.report_template_1'
   ↓
Calls ir.actions.report._render_qweb_pdf(res_ids=[order_id])
   ↓
HOOK: ir_actions_report._render_qweb_pdf_prepare_streams()
   - Checks: 'vpa_document_layout.report_template_' in report_ref
   - Sets context: vpa_force_zero_margins=True
   - Calls super() with new context
   ↓
Renders HTML via QWeb template
   ↓
HOOK: ir_actions_report._build_wkhtmltopdf_args()
   - Checks context.get('vpa_force_zero_margins')
   - Filters out --margin-* args
   - Adds: --margin-top 0 --margin-bottom 0 --margin-left 0 --margin-right 0
   ↓
Executes: wkhtmltopdf [args] input.html output.pdf
   ↓
Returns PDF bytes with ZERO physical margins
```

---

## Key Components

### 1. **vpa_document_template.py** - Template Model

#### Key Methods:

```python
def _create_report_action(self):
    """Creates ir.actions.report and paperformat"""
    # Gets model based on document_type
    # Creates/updates VPA A4 paperformat (zero margins!)
    # Creates report action with binding

def _create_qweb_template(self):
    """Generates QWeb templates dynamically"""
    # Builds external_layout_vpa_template_{id} with:
    #   - @page CSS with zero margins
    #   - Paper size from template.paper_size
    #   - Colors, logo, header, footer from template fields
    # Creates inheritance view to hijack web.external_layout

def _get_paper_dimensions(self):
    """Returns {'width': 210, 'height': 297} for A4"""

def _get_table_styles(self):
    """Returns CSS vars for table styling presets"""

def _compute_preview(self):
    """Generates live HTML preview"""
```

#### Critical Fields:

```python
# Paper Settings
paper_size = Selection(['a4', 'letter'])           # Paper format
paper_orientation = Selection(['portrait', 'landscape'])

# Report Binding
report_action_id = Many2one('ir.actions.report')  # Auto-created action
document_type = Selection([...])                   # Target document
target_app = Selection([...])                      # Target Odoo app

# Styling
primary_accent_color = Char(default='#875a7b')
header_logo_width/height = Integer
table_style = Selection([...])                     # Table preset
footer_layout = Selection([...])                   # Footer columns
```

### 2. **ir_actions_report.py** - PDF Generation Override

#### Key Methods:

```python
def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
    """
    ⭐ CRITICAL HOOK: Detects VPA templates and forces zero margins
    """
    is_vpa_template = 'vpa_document_layout.report_template_' in str(report_ref)

    if is_vpa_template:
        # Set context flag for zero margins
        return self.with_context(vpa_force_zero_margins=True)\
                  ._render_qweb_pdf_prepare_streams(report_ref, data, res_ids)

    return super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids)

def _build_wkhtmltopdf_args(self, paperformat_id, ...):
    """
    ⭐ CRITICAL HOOK: Modifies wkhtmltopdf arguments
    """
    command_args = super()._build_wkhtmltopdf_args(...)

    if self.env.context.get('vpa_force_zero_margins'):
        # Remove existing margin args
        command_args = [arg for arg in command_args
                       if not arg.startswith('--margin-')]

        # Force zero margins
        command_args.extend([
            '--margin-top', '0',
            '--margin-bottom', '0',
            '--margin-left', '0',
            '--margin-right', '0',
        ])

    return command_args
```

### 3. **controllers/main.py** - Preview Endpoints

```python
@http.route('/vpa/template/preview/<int:template_id>', auth='user')
def preview_template(self, template_id):
    """HTML live preview"""
    # Renders template_preview_fullpage template
    # Shows exact paper dimensions with gray background

@http.route('/vpa/template/preview/pdf/<int:template_id>', auth='user')
def preview_template_pdf(self, template_id):
    """PDF download preview"""
    # Finds sample sale.order
    # Generates PDF using report_action._render_qweb_pdf()
    # Returns PDF file for download
```

### 4. **_create_qweb_template()** - Template Generation

This method builds QWeb XML dynamically. Here's the structure:

```xml
<t t-name="vpa_document_layout.external_layout_vpa_template_{id}">
    <t t-set="vpa_template" t-value="env['vpa.document.template'].browse({id})"/>

    <div class="article o_report_layout_vpa">
        <style type="text/css">
            @page {
                margin: 0mm !important;
                size: A4 portrait;  /* Dynamic from template */
            }
            body {
                width: 210mm !important;  /* Dynamic from template.paper_size */
                height: 297mm !important;
            }
            /* Table styles from template.table_style preset */
        </style>

        <!-- Header with logo & company details -->
        <div style="border-bottom: 4px solid {primary_color}">
            <img t-att-src="image_data_uri(company.logo)"
                 style="max-width: {header_logo_width}px"/>
            <div t-out="vpa_template.header_company_details_html"/>
        </div>

        <!-- Customer & Document Info -->
        <table>
            <tr>
                <td><t t-out="address"/></td>
                <td><h2 t-out="layout_document_title"/></td>
            </tr>
        </table>

        <!-- Document Content Injection -->
        <t t-out="0"/>

        <!-- Footer -->
        <div style="position: absolute; bottom: 0;">
            <!-- Footer columns/content -->
        </div>
    </div>
</t>
```

**Key Substitutions**:
- `%s` placeholders filled via Python string formatting
- Colors, dimensions, alignment from template fields
- Conditional sections (t-if) for optional elements

---

## PDF Generation System

### wkhtmltopdf Argument Flow

**Standard Odoo**:
```bash
wkhtmltopdf --margin-top 40 --margin-bottom 35 --margin-left 7 --margin-right 7 \
            --header-spacing 35 --footer-spacing 10 \
            input.html output.pdf
```

**VPA Document Layout**:
```bash
wkhtmltopdf --margin-top 0 --margin-bottom 0 --margin-left 0 --margin-right 0 \
            input.html output.pdf
```

### Why Zero Margins?

1. **Full Control**: Template defines ALL spacing via CSS
2. **Pixel-Perfect**: No wkhtmltopdf default margins interfering
3. **Background Colors**: Can extend to page edges
4. **Decorative Elements**: Circles/waves can position absolutely

### CSS Page Definition

```css
@page {
    margin: 0mm !important;
    size: A4 portrait;  /* or Letter landscape */
}

html, body {
    width: 210mm !important;  /* A4 width */
    height: 297mm !important; /* A4 height */
    margin: 0 !important;
    padding: 0 !important;
}

.o_report_layout_vpa {
    width: 210mm;
    height: 297mm;
    padding: 20px;  /* Internal padding for content */
}
```

---

## Template System

### Dynamic QWeb Template Creation

When a template is created/updated, `_create_qweb_template()` generates:

#### 1. Main Report Template
```xml
<t t-name="vpa_document_layout.report_template_{id}">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="doc">
            <t t-call="sale.report_saleorder_document" t-lang="doc.partner_id.lang"/>
        </t>
    </t>
</t>
```

#### 2. External Layout Template
```xml
<t t-name="vpa_document_layout.external_layout_vpa_template_{id}">
    <!-- Full layout with header, footer, styling -->
    <!-- Injected via t-out="0" -->
</t>
```

#### 3. Inheritance View (XPath)
```xml
<xpath expr="//t[@t-call='web.external_layout']" position="attributes">
    <attribute name="t-call">vpa_document_layout.external_layout_vpa_template_{id}</attribute>
</xpath>
```

This **hijacks** the document template's call to `web.external_layout` and redirects to the VPA layout.

---

## Integration Points

### 1. **Odoo Report System**

**Entry Point**: `ir.actions.report`
- Each template creates a binding on its target model
- Appears in Print menu automatically
- Report name: `vpa_document_layout.report_template_{id}`

### 2. **Company Settings**

Via `res.company.external_report_layout_id`:
- OLD SYSTEM: Points to `vpa_document_layout.external_layout_vpa` (static)
- NEW SYSTEM: Each template has its own external_layout

### 3. **QWeb Rendering**

- Calls document template (e.g., `sale.report_saleorder_document`)
- Document template calls `web.external_layout`
- **Inheritance view intercepts** and calls VPA template instead
- VPA template wraps content with header/footer

---

## Troubleshooting

### Issue 1: PDF Returns 0 Bytes

**Symptoms**: Click "Download PDF Preview" → 0 byte file

**Causes**:
1. QWeb template not found
2. HTML renders but wkhtmltopdf fails
3. Sample data missing

**Debug Steps**:
```python
# In controllers/main.py, check logs:
docker-compose logs -f odoo --tail=100

# Look for:
# - "Report action: ..."
# - "Using sample order: ..."
# - "PDF generated, size: X bytes"

# If HTML renders but PDF empty:
# - Check wkhtmltopdf is installed
# - Test: docker-compose exec odoo wkhtmltopdf --version
```

### Issue 2: Margins Still Appearing

**Symptoms**: White margins in generated PDF despite zero-margin settings

**Causes**:
1. Context flag not being set
2. wkhtmltopdf args not being modified
3. Paperformat margins not zero

**Fix**:
```bash
# Check paperformat margins
python3 deep_check_pdf.py | grep "VPA A4" -A 5

# Should show: T:0.0, B:0.0, L:0.0, R:0.0

# Check context flag in logs
# Should see: "Forcing zero margins for VPA template (from context)"
```

### Issue 3: Template Not Appearing in Print Menu

**Causes**:
1. Report action not created
2. Wrong document_type/target_app
3. Model mismatch

**Fix**:
```python
# Check report action exists
template.report_action_id  # Should have value

# Check binding
template.report_action_id.binding_model_id  # Should match document type

# Regenerate if needed
template.action_regenerate_templates()
```

### Issue 4: Preview Shows Wrong Paper Size

**Causes**:
1. Paper dimensions not updating
2. Cache issue

**Fix**:
```python
# Force recompute preview
template._compute_preview()

# Or regenerate templates
template.action_regenerate_templates()
```

---

## Advanced Customization

### Adding New Table Styles

In `vpa_document_template.py`, edit `_get_table_styles()`:

```python
style_presets = {
    'my_custom_style': {
        'header_bg': '#your_color',
        'header_text': '#ffffff',
        'border': '#border_color',
        'alt_row': '#alternating_row_color',
        'header_border_bottom': '3px solid #accent',
    },
}
```

Then add to Selection field:
```python
table_style = fields.Selection([
    # ... existing styles
    ('my_custom_style', 'My Custom Style - Description'),
])
```

### Adding New Document Types

1. Add to `document_type` Selection
2. Update `model_map` in `_create_report_action()`
3. Update `document_template_map` in `_create_qweb_template()`

```python
# In _create_report_action()
model_map = {
    'my_new_doc': 'my.odoo.model',
}

# In _create_qweb_template()
document_template_map = {
    'my_new_doc': 'my_module.my_qweb_document_template',
}
```

---

## Summary

### What You've Mastered:

✅ **Module Structure**: Know every file's purpose
✅ **Template System**: How QWeb templates are generated dynamically
✅ **PDF Generation**: How zero-margin PDFs are created
✅ **Data Flow**: From template creation → PDF output
✅ **Integration**: How it hooks into Odoo's report system
✅ **Debugging**: How to troubleshoot common issues

### Key Takeaways:

1. **Two Models**: `vpa.document.template` (active) + `vpa.document.config` (legacy)
2. **Three QWeb Templates**: Main report + External layout + Inheritance view
3. **Two Hooks**: `_render_qweb_pdf_prepare_streams()` + `_build_wkhtmltopdf_args()`
4. **Zero Margins**: Achieved via context flag → wkhtmltopdf args modification
5. **Dynamic Generation**: Templates built via Python string formatting in `_create_qweb_template()`

---

**You are now a VPA Document Layout Master! 🎓**
