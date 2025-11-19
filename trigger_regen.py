import odoo
from odoo import api
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf', '-d', 'odoo'])

registry = Registry('odoo')
with registry.cursor() as cr:
    env = api.Environment(cr, odoo.SUPERUSER_ID, {'bin_size': False})

    template = env['vpa.document.template'].browse(3)
    print(f"Template: {template.name}")
    print(f"Company: {template.company_id.name}")

    # Check if logo field exists
    print(f"Has logo field: {hasattr(template, 'logo')}")
    if hasattr(template, 'logo'):
        print(f"Logo exists: {bool(template.logo)}")
        if template.logo:
            print(f"Logo size: {len(template.logo)} bytes")

    # Force regeneration
    print("\nRegenerating templates...")
    template.action_regenerate_templates()

    # Commit changes
    cr.commit()

    # Verify templates were created
    views = env['ir.ui.view'].search([
        ('key', 'like', '%vpa_template_3%')
    ])

    print(f"\n✓ Created {len(views)} QWeb views:")
    for view in views:
        print(f"  - {view.name} (key: {view.key})")

    print("\n✓ SUCCESS: Templates regenerated!")
