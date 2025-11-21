#!/usr/bin/env python3
"""
Script to add screenshot placeholders to the index.html file
"""

import re

# Read the current HTML file
with open('static/description/index.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Define screenshots to insert
screenshots = {
    # After overview description
    'overview_end': '''
        <!-- Hero Screenshot -->
        <div style="text-align: center; margin: 40px 0; padding: 30px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 15px;">
            <img src="banner.png" alt="VPA MO Link - Complete Overview"
                 class="screenshot"
                 onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'1200\' height=\'400\'%3E%3Crect fill=\'%232874A6\' width=\'1200\' height=\'400\'/%3E%3Ctext fill=\'white\' font-family=\'Arial\' font-size=\'40\' font-weight=\'bold\' x=\'50%25\' y=\'50%25\' text-anchor=\'middle\' dy=\'.3em\'%3EVPA - Manufacturing Order Link%3C/text%3E%3C/svg%3E'">
            <p style="color: #666; font-style: italic; margin-top: 15px; font-size: 1.1em;">Seamless integration with Odoo Sales and Manufacturing</p>
        </div>
''',

    # After Key Features section
    'features_end': '''
        <!-- Feature Screenshots Grid -->
        <div style="margin: 50px 0;">
            <h3 style="color: #2874A6; text-align: center; font-size: 1.8em; margin-bottom: 30px;">📸 See It In Action</h3>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 30px; margin-top: 30px;">
                <!-- Smart Button Screenshot -->
                <div style="background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <img src="screenshot_smart_button.png" alt="Manufacturing Smart Button" class="screenshot"
                         onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'800\' height=\'500\'%3E%3Crect fill=\'%238E44AD\' width=\'800\' height=\'500\'/%3E%3Ctext fill=\'white\' font-family=\'Arial\' font-size=\'32\' x=\'50%25\' y=\'45%25\' text-anchor=\'middle\'%3EManufacturing Smart Button%3C/text%3E%3Ctext fill=\'white\' font-family=\'Arial\' font-size=\'18\' x=\'50%25\' y=\'55%25\' text-anchor=\'middle\' opacity=\'0.9\'%3EUnified MO Display%3C/text%3E%3C/svg%3E'">
                    <h4 style="color: #8E44AD; margin-top: 15px;">Unified Smart Button</h4>
                    <p style="color: #666;">All Manufacturing Orders in one place - both automatic and manual</p>
                </div>

                <!-- MO Link Action Screenshot -->
                <div style="background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <img src="screenshot_mo_link_action.png" alt="MO Link Action" class="screenshot"
                         onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'800\' height=\'500\'%3E%3Crect fill=\'%232874A6\' width=\'800\' height=\'500\'/%3E%3Ctext fill=\'white\' font-family=\'Arial\' font-size=\'32\' x=\'50%25\' y=\'45%25\' text-anchor=\'middle\'%3EMO - Link Action%3C/text%3E%3Ctext fill=\'white\' font-family=\'Arial\' font-size=\'18\' x=\'50%25\' y=\'55%25\' text-anchor=\'middle\' opacity=\'0.9\'%3EOne-Click Manual Linking%3C/text%3E%3C/svg%3E'">
                    <h4 style="color: #2874A6; margin-top: 15px;">MO - Link/Unlink Actions</h4>
                    <p style="color: #666;">Easy manual control over MO-SO relationships</p>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 30px; margin-top: 30px;">
                <!-- Draft MO Screenshot -->
                <div style="background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <img src="screenshot_mo_draft.png" alt="MO in Draft State" class="screenshot"
                         onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'800\' height=\'500\'%3E%3Crect fill=\'%2328a745\' width=\'800\' height=\'500\'/%3E%3Ctext fill=\'white\' font-family=\'Arial\' font-size=\'32\' x=\'50%25\' y=\'45%25\' text-anchor=\'middle\'%3EMO in DRAFT State%3C/text%3E%3Ctext fill=\'white\' font-family=\'Arial\' font-size=\'18\' x=\'50%25\' y=\'55%25\' text-anchor=\'middle\' opacity=\'0.9\'%3EReview Before Confirm%3C/text%3E%3C/svg%3E'">
                    <h4 style="color: #28a745; margin-top: 15px;">Draft MO Creation</h4>
                    <p style="color: #666;">All MOs stay in DRAFT for your review and approval</p>
                </div>

                <!-- No BOM Screenshot -->
                <div style="background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <img src="screenshot_no_bom.png" alt="MO Without BOM" class="screenshot"
                         onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'800\' height=\'500\'%3E%3Crect fill=\'%23ffc107\' width=\'800\' height=\'500\'/%3E%3Ctext fill=\'%23333\' font-family=\'Arial\' font-size=\'32\' x=\'50%25\' y=\'45%25\' text-anchor=\'middle\'%3EMO Without BOM%3C/text%3E%3Ctext fill=\'%23333\' font-family=\'Arial\' font-size=\'18\' x=\'50%25\' y=\'55%25\' text-anchor=\'middle\' opacity=\'0.8\'%3ESet BOM After Creation%3C/text%3E%3C/svg%3E'">
                    <h4 style="color: #ffc107; margin-top: 15px;">No-BOM Support</h4>
                    <p style="color: #666;">Create MOs even when BOM doesn't exist yet</p>
                </div>
            </div>
        </div>
''',

    # After Workflows section
    'workflows_end': '''
        <!-- Configuration Screenshots -->
        <div style="margin: 50px 0; padding: 40px; background: #f8f9fa; border-radius: 15px;">
            <h3 style="color: #2874A6; text-align: center; font-size: 1.8em; margin-bottom: 30px;">⚙️ Easy Configuration</h3>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; align-items: center;">
                <div>
                    <img src="screenshot_production_route.png" alt="Production Route Configuration" class="screenshot"
                         onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'800\' height=\'500\'%3E%3Crect fill=\'%23C0392B\' width=\'800\' height=\'500\'/%3E%3Ctext fill=\'white\' font-family=\'Arial\' font-size=\'32\' x=\'50%25\' y=\'45%25\' text-anchor=\'middle\'%3EProduction Route%3C/text%3E%3Ctext fill=\'white\' font-family=\'Arial\' font-size=\'18\' x=\'50%25\' y=\'55%25\' text-anchor=\'middle\' opacity=\'0.9\'%3ESimple Product Setup%3C/text%3E%3C/svg%3E'">
                </div>
                <div>
                    <h4 style="color: #C0392B; font-size: 1.6em;">Production Route</h4>
                    <p style="font-size: 1.1em; line-height: 1.8; color: #555;">
                        Simply check the <strong>"Production"</strong> route on your product's Inventory tab,
                        and the module handles the rest. No complex configuration needed!
                    </p>
                    <ul style="font-size: 1.05em; color: #666; line-height: 1.8;">
                        <li>✓ Created automatically on installation</li>
                        <li>✓ Product-selectable for easy assignment</li>
                        <li>✓ Works with multi-warehouse setups</li>
                        <li>✓ Compatible with standard Manufacture route</li>
                    </ul>
                </div>
            </div>
        </div>
''',

    # After Comparison Table
    'comparison_end': '''
        <!-- Real-World Example Screenshots -->
        <div style="margin: 50px 0;">
            <h3 style="color: #2874A6; text-align: center; font-size: 1.8em; margin-bottom: 30px;">💼 Real-World Usage</h3>

            <div style="background: white; border: 2px solid #2874A6; border-radius: 15px; padding: 30px; margin-bottom: 30px;">
                <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 30px; align-items: center;">
                    <div>
                        <img src="screenshot_mo_list.png" alt="Manufacturing Orders List" class="screenshot"
                             onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'1000\' height=\'600\'%3E%3Crect fill=\'%232874A6\' width=\'1000\' height=\'600\'/%3E%3Ctext fill=\'white\' font-family=\'Arial\' font-size=\'36\' x=\'50%25\' y=\'45%25\' text-anchor=\'middle\'%3EManufacturing Orders List%3C/text%3E%3Ctext fill=\'white\' font-family=\'Arial\' font-size=\'20\' x=\'50%25\' y=\'55%25\' text-anchor=\'middle\' opacity=\'0.9\'%3ELinked to Sales Order%3C/text%3E%3C/svg%3E'">
                    </div>
                    <div>
                        <h4 style="color: #2874A6; font-size: 1.5em;">Complete Visibility</h4>
                        <p style="color: #666; font-size: 1.05em; line-height: 1.7;">
                            Click the smart button to instantly view all Manufacturing Orders linked to your Sales Order.
                            See production status, origin, quantities, and more at a glance.
                        </p>
                    </div>
                </div>
            </div>

            <div style="background: white; border: 2px solid #8E44AD; border-radius: 15px; padding: 30px;">
                <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 30px; align-items: center;">
                    <div>
                        <h4 style="color: #8E44AD; font-size: 1.5em;">Audit Trail</h4>
                        <p style="color: #666; font-size: 1.05em; line-height: 1.7;">
                            Complete traceability with chatter integration. Every link, unlink, and creation
                            is logged with timestamps and clickable references.
                        </p>
                    </div>
                    <div>
                        <img src="screenshot_chatter_link.png" alt="Chatter Audit Trail" class="screenshot"
                             onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'700\' height=\'400\'%3E%3Crect fill=\'%238E44AD\' width=\'700\' height=\'400\'/%3E%3Ctext fill=\'white\' font-family=\'Arial\' font-size=\'28\' x=\'50%25\' y=\'45%25\' text-anchor=\'middle\'%3EChatter Integration%3C/text%3E%3Ctext fill=\'white\' font-family=\'Arial\' font-size=\'16\' x=\'50%25\' y=\'55%25\' text-anchor=\'middle\' opacity=\'0.9\'%3EComplete Audit Trail%3C/text%3E%3C/svg%3E'">
                    </div>
                </div>
            </div>
        </div>
''',
}

# Insert screenshots at appropriate locations
# After overview (find the closing </div> of overview section)
pattern_overview = r'(where BOMs are defined after order confirmation\.\s*</p>\s*</div>)'
replacement_overview = r'\1' + screenshots['overview_end']
html_content = re.sub(pattern_overview, replacement_overview, html_content, count=1)

# After features section (find closing of feature-grid)
pattern_features = r'(</div>\s*</div>\s*<!-- Workflows Section -->)'
replacement_features = screenshots['features_end'] + r'\1'
html_content = re.sub(pattern_features, replacement_features, html_content, count=1)

# After workflows (find the end of workflow containers)
pattern_workflows = r'(</div>\s*</div>\s*</div>\s*<!-- Why Choose This Module -->)'
replacement_workflows = screenshots['workflows_end'] + r'\1'
html_content = re.sub(pattern_workflows, replacement_workflows, html_content, count=1)

# After comparison table
pattern_comparison = r'(</table>\s*</div>\s*<!-- Technical Details -->)'
replacement_comparison = screenshots['comparison_end'] + r'\1'
html_content = re.sub(pattern_comparison, replacement_comparison, html_content, count=1)

# Write the updated HTML
with open('static/description/index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("✅ Screenshots added successfully to index.html!")
print("\n📸 Required screenshot files:")
print("  - banner.png")
print("  - screenshot_smart_button.png")
print("  - screenshot_mo_link_action.png")
print("  - screenshot_mo_draft.png")
print("  - screenshot_no_bom.png")
print("  - screenshot_production_route.png")
print("  - screenshot_mo_list.png")
print("  - screenshot_chatter_link.png")
print("\n💡 Placeholder images will show if screenshots are missing")
print("📁 Place screenshots in: static/description/")
