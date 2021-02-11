# -*- coding: utf-8 -*-
#############################################################################
#
#    Madfox Solutions
#
#    Copyright (C) 2021-TODAY Madfox Solutions(<https://www.madfox.solutions>).
#    Author: Mohamad MOaiad Bashiti (moaiad@madfox.solutions)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': 'Fashion Gala Customization',
    'version': '14.0.1.0.0',
    'summary': 'Generates internal refrernce number and Barcode for Product.',
    'category': 'Inventory',
    'author': 'Madfox',
    'maintainer': 'Madfox solutions',
    'company': 'Madfox solutions',
    'website': 'https://www.madfox.solutions',
    'depends': ['stock', 'product'],
    'data': [
        'views/product_label.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': True,
}
