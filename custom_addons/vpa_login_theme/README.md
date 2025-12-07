# VPA Login Theme

Transform your Odoo login page with custom branding, colors, and favicon!

## Features

### 🎨 Easy Color Customization
- **6 Pre-built Themes**: Red, Blue, Green, Purple, Orange, and Dark
- **Custom Color Picker**: Create unlimited color combinations
- **Live HTML Preview**: See exactly how your login page will look
- **Border Radius Control**: Customize button and input styling

### 🖼️ Branding & Logo
- **Custom Favicon Support**: Upload your own .ico or .png favicon
- **Company Logo Display**: View and manage your company logo
- **Logo Size Controls**: Adjust height (pixels) and width (percentage)
- **Welcome Message**: Add custom greeting to login page
- **Page Title**: Customize browser tab title
- **Footer Text**: Add copyright and company information

### 🏢 Multi-Company Support
- Different themes for different companies
- Company-specific branding
- Perfect for multi-tenant installations

### ⚡ Easy to Use
- User-friendly settings interface with tabs
- No coding required
- Changes apply instantly
- Professional branded interface

## Installation

1. Copy the `vpa_login_theme` folder to your Odoo custom addons directory
2. Restart your Odoo server
3. Update the Apps list (Apps → Update Apps List)
4. Search for "VPA Login Theme"
5. Click Install

## Configuration

### Access Control

Only users with proper permissions can configure themes:
- **System Administrators**: Full access by default
- **Login Theme Manager**: Custom role with theme configuration access

To grant access to other users:
1. Go to **Settings → Users & Companies → Users**
2. Select the user
3. Under **Access Rights** tab, enable **Login Theme / Login Theme Manager**
4. Save

### Theme Configuration

1. Go to **Settings → VPA Applications → Login Theme**
2. **Colors & Styling Tab**:
   - Select **Preset Theme** from dropdown for quick themes
   - Or use **color pickers** to customize each element
   - Adjust **Border Radius** for button styling
3. **Branding & Content Tab**:
   - View your current **company logo**
   - Upload **custom favicon** (.ico or .png, 16x16 or 32x32 px recommended)
   - Add **welcome message** and **footer text**
   - Adjust **logo display settings** (height in px, width in %)
4. **Advanced Settings Tab**:
   - Control **database selector** visibility
5. **Preview Tab**:
   - See **live HTML preview** of your login page
   - Hover over login button to see hover effects
6. Click **Save**
7. Refresh your login page to see the changes!

## Color Options

### Pre-built Themes

| Theme | Primary Color | Use Case |
|-------|--------------|----------|
| **Red** | #DC143C | Bold, energetic brands |
| **Blue** | #1E40AF | Professional, corporate |
| **Green** | #059669 | Eco-friendly, growth |
| **Purple** | #7C3AED | Creative, modern (Odoo default) |
| **Orange** | #EA580C | Friendly, warm |
| **Dark** | #1F2937 | Elegant, minimal |

### Custom Colors

Use the color picker widgets to set:
- **Primary Color**: Login button background
- **Secondary Color**: Hover and active states
- **Link Color**: Text links on login page
- **Background Color**: Page background

## Logo Settings

- **Logo Max Height**: Maximum height in pixels (default: 120px)
- **Logo Max Width**: Maximum width as percentage (default: 100%)

## Screenshots

### Settings Interface
Easy-to-use configuration panel with live preview

### Multiple Themes
Choose from 6 pre-built themes or create your own

### Live Preview
See your changes before applying them

## Support

For issues, feature requests, or questions:
- **Email**: support@vpa-solutions.com
- **Website**: https://www.vpa-solutions.com

## Version History

### Version 19.0.1.0.0
- Initial release for Odoo 19
- 6 pre-built color themes
- Custom color picker for all elements
- Custom favicon upload support
- Logo size controls
- Welcome message and footer text
- Page title customization
- Border radius controls
- Multi-company support
- Live HTML preview with interactive elements
- Professional tabbed interface
- Role-based access control

## License

LGPL-3 - See LICENSE file for full copyright and licensing details.

## Author

**VPA Software Limited**
- Website: https://www.vpa-solutions.com
- Email: support@vpa-solutions.com

---

**Make your Odoo login page truly yours!** 🚀
