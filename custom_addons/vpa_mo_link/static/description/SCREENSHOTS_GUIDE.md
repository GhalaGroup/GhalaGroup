# Screenshot Guide for VPA - Manufacturing Order Link

## Required Screenshots for index.html

To complete the visual documentation, please take the following screenshots and save them in the `static/description/` folder:

### 1. **banner.png** (Main Banner Image)
- **Recommended Size:** 1200x400px
- **Content:** Wide shot showing the Sales Order form with the Manufacturing smart button visible
- **Purpose:** Hero image at the top of the page

### 2. **screenshot_smart_button.png**
- **Recommended Size:** 800x500px
- **What to Show:**
  - Sales Order form
  - Manufacturing smart button with count (e.g., "3 Manufacturing")
  - Highlight the button with a red circle or arrow
- **Purpose:** Show the main feature - unified smart button

### 3. **screenshot_mo_link_action.png**
- **Recommended Size:** 800x500px
- **What to Show:**
  - Sales Order form
  - Action menu dropdown open
  - "MO - Link" and "MO - Unlink" actions visible
  - Highlight with arrows
- **Purpose:** Demonstrate manual linking actions

### 4. **screenshot_mo_draft.png**
- **Recommended Size:** 800x500px
- **What to Show:**
  - Manufacturing Order in DRAFT state
  - Show product, quantity, BOM fields
  - Highlight the DRAFT status badge
- **Purpose:** Show that MOs stay in DRAFT for review

### 5. **screenshot_no_bom.png**
- **Recommended Size:** 800x500px
- **What to Show:**
  - Manufacturing Order created without BOM
  - Empty BOM field with option to set it
  - Warning message in chatter (if visible)
- **Purpose:** Demonstrate no-BOM support feature

### 6. **screenshot_production_route.png**
- **Recommended Size:** 800x500px
- **What to Show:**
  - Product form → Inventory tab
  - Routes section with "Production" route checked
  - Highlight the Production route
- **Purpose:** Show route configuration

### 7. **screenshot_mo_list.png**
- **Recommended Size:** 1000x600px
- **What to Show:**
  - List of Manufacturing Orders accessed from SO smart button
  - Multiple MOs visible
  - Origin column showing SO name
- **Purpose:** Show the linked MOs view

### 8. **screenshot_chatter_link.png**
- **Recommended Size:** 700x400px
- **What to Show:**
  - Chatter/activity section
  - Message showing "Linked Manufacturing Orders: MO001, MO002"
  - Clickable links in blue
- **Purpose:** Show audit trail and traceability

## How to Add Screenshots:

1. **Take screenshots** following the guide above
2. **Save files** in: `/custom_addons/vpa_mo_link/static/description/`
3. **File naming** must match exactly:
   - banner.png
   - screenshot_smart_button.png
   - screenshot_mo_link_action.png
   - screenshot_mo_draft.png
   - screenshot_no_bom.png
   - screenshot_production_route.png
   - screenshot_mo_list.png
   - screenshot_chatter_link.png

4. **Image optimization:**
   - Use PNG format for clarity
   - Compress images to keep file size reasonable (< 500KB each)
   - Ensure text is readable at reduced sizes

## Alternative: Use Placeholder Images

If screenshots are not ready, you can use placeholder images temporarily:
- Create simple colored rectangles with text
- Use online tools like placeholder.com
- Example: `https://via.placeholder.com/800x500/2874A6/FFFFFF?text=Screenshot+Coming+Soon`

The HTML file is already configured to display these images in the appropriate sections.
