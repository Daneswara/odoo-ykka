# -*- coding: utf-8 -*-
{
    'name': "KA Logistik RAB",

    'summary': """
        Logistik - RAB""",

    'description': """
        Logistik RAB\n
        - Rencana Pemakaian\n
        - Rencana Pengadaan
    """,

    'author': "PT. Kebon Agung",
    'website': "http://ptkebonagung.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'ka_logistik_master', 'ka_analytic_stasiun', 'ka_report_layout'],

    # always loaded
    'data': [
        'security/logistik_rab.xml',
        'security/ir.model.access.csv',
        'views/logistik_rab.xml',
    ],
}