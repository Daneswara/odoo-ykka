# -*- coding: utf-8 -*-
{
    'name': "KA Logistik Master",

    'summary': """
        Logistik - Pemeliharaan File Master""",

    'description': """
        Modul ini digunakan untuk mengatur file-file master: \n
        - Master Rekanan\n
        - Barang gudang(LOG1A1)\n
        - Satuan Gudang (LOG1A3)\n 
        - Unit Pemakai Barang(LOG1A2)\n
        - Master STTB(LOG1A4)
    """,

    'author': "PT. Kebon Agung",
    'website': "http://ptkebonagung.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'purchase', 'sale', 'account', 'account_accountant'],

    # always loaded
    'data': [
        'views/logistik_master.xml',
        'views/product.xml',
        'views/res_partner.xml',
		'wizard/product_update_hps_view.xml',
        'security/logistik_master.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}