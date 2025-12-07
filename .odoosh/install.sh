#!/bin/bash
# odoo.sh post-deployment install script
# This script runs after every push to odoo.sh

set -e

echo "=========================================="
echo "VPA Login Theme - Post-Deployment Install"
echo "=========================================="

# Check if module is already installed
if odoo-bin shell -d "$ODOO_DB" --no-http << EOF
module = env['ir.module.module'].search([('name', '=', 'vpa_login_theme')])
if module and module.state == 'installed':
    print("ALREADY_INSTALLED")
    exit(0)
else:
    print("NOT_INSTALLED")
    exit(1)
EOF
then
    echo "✓ VPA Login Theme already installed"
else
    echo "Installing VPA Login Theme..."
    odoo-bin -d "$ODOO_DB" -i vpa_login_theme --stop-after-init --no-http
    echo "✓ VPA Login Theme installed successfully"
fi

echo "=========================================="
echo "Post-deployment complete"
echo "=========================================="
