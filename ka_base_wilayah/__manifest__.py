# -*- coding: utf-8 -*-
{
    'name': "Base Wilayah Indonesia",

    'summary': """
        Data wilayah yang ada di Indonesia""",

    'description': """
        Data Wilayah yang ada di Indonesia\n
        - Kelurahan\n
        - Kecamatan\n
        - Kota / Kabupaten\n
        - Provinsi
    """,

    'author': "Nerita",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Base',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/base_wilayah.xml',
        'security/ir.model.access.csv',
        'views/desa_kelurahan.xml',
        'views/kecamatan.xml',
        'views/kab_kota.xml',
        'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}