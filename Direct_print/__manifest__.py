# -*- coding: utf-8 -*-
#############################################################################
#
#    Madfox Solutions
#
#    Copyright (C) 2021-TODAY Madfox Solutions(<https://www.madfox.solutions>).
#    Author: Layla Bahloul
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
    'name': 'Direct Print',
    'version': '15.0.1.0.0',
    'summary': 'Prints zpls directly to the printer',
    'category': 'Inventory',
    'author': 'Madfox',
    'maintainer': 'Madfox solutions',
    'company': 'Madfox solutions',
   'website': 'https://www.madfox.solutions',
    'depends': ['stock', 'product','web','sale'],

    
    # 'data': [
    #     'views/assets.xml'
    # ],
     'assets': { 
         'web.assets_backend': [ 
             
             'Direct_print/static/src/js/BrowserPrint-3.0.216.min.js',
             'Direct_print/static/src/js/BrowserPrint-Zebra-1.0.216.min.js',
             'Direct_print/static/src/js/zpl_print.js',
         ] 
     } ,
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': True,
    
}

