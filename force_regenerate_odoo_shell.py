"""Force regenerate all VPA templates - Run this with: odoo shell -d odoo"""

print("=" * 80)
print("FORCE REGENERATING ALL VPA TEMPLATES")
print("=" * 80)

# Find all VPA templates
templates = env['vpa.document.template'].search([])
print(f"\nFound {len(templates)} VPA templates:")
for t in templates:
    print(f"  - Template {t.id}: {t.name}")

# Find ALL views related to VPA templates
all_views = env['ir.ui.view'].search([
    '|', '|', '|',
    ('key', 'like', '%vpa_template%'),
    ('key', 'like', '%template_%'),
    ('key', 'like', '%inherit_%'),
    ('name', 'like', '%VPA%')
])

print(f"\nFound {len(all_views)} VPA-related views in database:")
for v in all_views:
    print(f"  - View {v.id}: {v.name} (key: {v.key})")
    # Check if it has footer content
    arch_str = str(v.arch or '')
    if 'footer-wave' in arch_str or 'footer-cell' in arch_str:
        print(f"    ⚠️  THIS VIEW HAS FOOTER CONTENT!")
        print(f"    Last 300 chars: {arch_str[-300:]}")

print("\nDeleting all VPA template views...")
all_views.unlink()
print(f"✅ Deleted {len(all_views)} views")

print("\nRegenerating templates...")
for t in templates:
    print(f"  Regenerating template {t.id}: {t.name}")
    t._create_qweb_template()

# Check what was created
new_views = env['ir.ui.view'].search([
    '|', '|',
    ('key', 'like', '%template_%'),
    ('key', 'like', '%inherit_%'),
    ('name', 'like', '%VPA%')
])

print(f"\n✅ Created {len(new_views)} new views:")
for v in new_views:
    print(f"  - View {v.id}: {v.name} (key: {v.key})")
    # Check if it has footer content
    arch_str = str(v.arch or '')
    has_footer = 'footer-wave' in arch_str or 'footer-cell' in arch_str
    if has_footer:
        print(f"    ⚠️  WARNING: NEW VIEW STILL HAS FOOTER CONTENT!")
        print(f"    Last 500 chars: {arch_str[-500:]}")
    else:
        print(f"    ✅ No footer content (correct!)")
        print(f"    Last 200 chars: {arch_str[-200:]}")

env.cr.commit()
print("\n" + "=" * 80)
print("REGENERATION COMPLETE!")
print("=" * 80)
