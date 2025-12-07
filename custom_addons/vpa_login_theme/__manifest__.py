{
    'name': 'VPA Login Theme',
    'version': '19.0.1.2.0',
    'category': 'Website/Website',
    'summary': 'Customize login page colors, branding, logo & favicon. 6 pre-built themes. Live preview. No coding!',
    'description': """
VPA Login Theme - Professional Branding for Your Odoo Login Page
=================================================================

Transform your Odoo login page with custom branding in minutes!

Key Features
------------
* **6 Pre-built Professional Themes**: Red, Blue, Green, Purple, Orange, Dark
* **Unlimited Custom Colors**: Built-in color picker for perfect brand matching
* **Custom Favicon Support**: Upload your own favicon (.ico, .png)
* **Live HTML Preview**: See exactly how your login page will look
* **Logo Controls**: Adjust logo size and positioning
* **Welcome Message**: Add custom text to your login page
* **Page Title Customization**: Change browser tab title
* **Footer Branding**: Add copyright and company info
* **Border Radius Control**: Customize button and input styling
* **Multi-Company Support**: Different themes per company
* **Role-Based Access Control**: Only authorized users can change themes
* **No Coding Required**: User-friendly settings interface
* **Instant Apply**: No server restart needed

Perfect For
-----------
* Corporate branding and identity
* White-labeling for agencies and resellers
* Multi-tenant installations
* Professional Odoo deployments
* Custom client branding

Easy Configuration
------------------
1. Go to Settings → VPA Applications → Login Theme
2. Choose a preset theme or customize colors
3. Upload custom favicon (optional)
4. Add welcome message and footer text
5. Adjust logo settings
6. View live preview
7. Save and enjoy your branded login page!

Access Control
--------------
Professional security with role-based permissions:
* System Administrators: Full access by default
* Login Theme Manager: Custom role for theme configuration
* Login Theme User: Read-only access
* Regular Users: No access (protected)

Grant access via Settings → Users & Companies → Users → Access Rights

Technical Details
-----------------
* Compatible with Odoo 19.0
* Works with Community and Enterprise editions
* No external dependencies
* Lightweight and performant
* Database-driven configuration
* Clean architecture following Odoo best practices

Support
-------
* Comprehensive documentation included
* Email support: support@vpa-solutions.com
* Regular updates and improvements
* Active maintenance and bug fixes

Make your Odoo login page truly yours with VPA Login Theme!
    """,
    'author': 'VPA Software Limited',
    'website': 'https://www.vpa-solutions.com',
    'maintainer': 'VPA Software Limited',
    'support': 'support@vpa-solutions.com',
    'license': 'LGPL-3',
    'price': 25.00,
    'currency': 'USD',
    'images': ['static/description/icon.png'],
    'depends': ['web'],
    'data': [
        'security/login_theme_security.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/login_theme_config_views.xml',
        'views/web_templates.xml',
        'data/default_theme_data.xml',
        'data/fix_menu_groups.xml',  # MUST be last to force menu groups
    ],
    'assets': {
        'web.assets_frontend': [
            'vpa_login_theme/static/src/css/login_theme.css',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
