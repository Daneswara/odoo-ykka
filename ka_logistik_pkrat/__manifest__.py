# -*- coding: utf-8 -*-
{
    'name': "KA Logistik - SP Kontrak (PKRAT)",

    'summary': """
        Logistik PKRAT - INVESTASI""",

    'description': """
        Logistik PKRAT - INVESTASI
    """,

    'author': "PDE PT. Kebon Agung",
    'website': "http://ptkebonagung.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['ka_base', 
                'ka_logistik_master', 
                'ka_analytic_stasiun', 
                'ka_report_layout',],

    # always loaded
    'data': [
        'security/logistik_pkrat.xml',
        'security/ir.model.access.csv',
        'views/logistik_pkrat.xml',
    ],
}