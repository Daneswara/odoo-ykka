# -*- coding: utf-8 -*-
{
    'name': "KA - Surat Pesanan",

    'summary': """
        KA - Surat Pesanan""",

    'description': """
        KA - Surat Pesanan
    """,

    'author': "PT. KA",
    'website': "http://ptkebonagung.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Logistik',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'ka_purchase', 'ka_logistik_spm', 'ka_report_layout'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/logistik_sp_cancel.xml',
#         'views/product.xml',
        'views/res_partner.xml',
        'views/logistik_spm.xml',
        'views/logistik_sp.xml',
#         'report/sp.xml',
#         'report/sp_konsep.xml',
#         'report/sp_sementara.xml',
#         'report/sp_tandaterima.xml',
#         'report/deleted_report.xml',
    ],
}