# VPA Document Layout

Custom document layout module for Odoo 19 with advanced customization options.

## Features

- **Universal Layout**: Works across all Odoo apps (Sales, Purchase, Invoices, Manufacturing, etc.)
- **Live Preview**: See changes in real-time as you configure
- **Customizable Header**: Logo positioning, company details, tagline, decorative shapes
- **Flexible Footer**: Multiple layout modes (centered, split, custom multi-row)
- **Custom HTML Sections**: Add your own HTML content to header and footer rows
- **Table Styling**: Choose between Bubble (rounded), Striped, Bordered, or Plain styles
- **Color Customization**: Primary/secondary accent colors, text colors for header/body/footer

## Installation

1. Copy this module to your Odoo `custom_addons` directory
2. Update Apps List: Settings → Apps → Update Apps List
3. Install: Search for "VPA Document Layout" and click Install
4. Configure: Access via "VPA Layout" menu in the app drawer

## How to Use

### Step 1: Configure Your Layout

1. Open the **VPA Layout** app from the app drawer
2. Configure your preferences:
   - **Header Tab**: Logo size/position, company details, decorative circles
   - **Footer Tab**: Layout mode, bank details, custom HTML rows
   - **Document Layout Tab**: Table styling, title positioning, customer address

### Step 2: Enable VPA Layout for Reports

1. Go to **Settings → Companies → Your Company**
2. Click **Configure Document Layout** button
3. From the layout selector, choose **"VPA Document Layout"**
4. Click **Save**

### Step 3: Generate Reports

Now when you generate any report (Sale Order, Invoice, etc.), it will automatically use your VPA layout:

- **Sales**: Create quotation → Print → Quotation / Pro-forma Invoice
- **Invoices**: Create invoice → Print → Invoice
- **Purchase**: Create purchase order → Print → Purchase Order
- **Any other report**: Will use VPA layout automatically

## Custom HTML Sections

The VPA layout supports custom HTML sections for maximum flexibility:

### Header Custom Sections
Enable "Custom Header Sections" in the Header tab to add up to 3 custom HTML rows above the standard header.

### Footer Custom Sections
1. In the Footer tab, select **Footer Layout Mode: Custom**
2. Enable **Custom Sections**
3. Configure up to 3 footer rows:
   - **Row 1**: Typically company/bank information
   - **Row 2**: Contact details
   - **Row 3**: Additional information

Each row can be:
- **Left-aligned**: Single HTML field aligned left
- **Center-aligned**: Single HTML field centered
- **Right-aligned**: Single HTML field aligned right
- **Split**: Two columns (left and right)

Example HTML for footer:
```html
<strong>Bank Account Details:</strong>
<p>Account Name: UDESIGN LIMITED<br/>
Bank: CRDB Bank<br/>
Account Number (TZS): 0150548871900</p>
```

## Architecture

### No Duplicate Headers/Footers

The VPA layout is designed following Odoo's standard external layout pattern:

1. Reports call `web.external_layout` (Odoo's router template)
2. The router checks company's `external_report_layout_id` setting
3. If "VPA Document Layout" is selected, it calls `vpa_document_layout.external_layout_vpa`
4. The VPA template wraps the report content with header and footer **exactly once**
5. Content is injected via `<t t-out="0"/>` between header and footer

This architecture ensures:
- ✅ No duplicate headers or footers
- ✅ Works universally across all Odoo reports
- ✅ Follows Odoo's standard pattern
- ✅ Compatible with custom report modules

### File Structure

```
vpa_document_layout/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── vpa_document_config.py        # Configuration model with live preview
├── views/
│   ├── vpa_config_views.xml          # Configuration form with side-by-side preview
│   ├── report_templates.xml          # Main VPA external layout template
│   ├── preview_template.xml          # Preview rendering templates
│   └── menu_workaround.xml           # Menu entries
├── data/
│   ├── report_layout.xml             # Registers VPA layout in report.layout
│   └── default_config.xml            # Creates default configuration
├── security/
│   └── ir.model.access.csv           # Access rights
└── static/
    └── description/
        └── icon.png                  # Module icon
```

## Troubleshooting

### Preview not showing changes
- Ensure all fields are in the `@api.depends` decorator in `vpa_document_config.py`
- Clear browser cache and Odoo cache: Settings → Technical → Database Structure → Clear assets cache

### Logo not displaying
- Check company logo is uploaded: Settings → Companies → Your Company → Upload logo
- Verify `image_data_uri` is imported from `odoo.tools.image`
- Ensure preview loads logo with `bin_size=False` context

### Layout not applying to reports
- Verify you selected "VPA Document Layout" in Settings → Companies → Configure Document Layout
- Check `company.external_report_layout_id` points to `vpa_document_layout.external_layout_vpa`
- Restart Odoo and regenerate report

### Custom sections not appearing
- Ensure "Custom Sections" is enabled in Footer tab
- Check that row is enabled (e.g., "Footer Row 1 Enable")
- Verify HTML content is not empty
- Preview in HTML mode first before generating PDF

## License

LGPL-3

## Author

VPA
