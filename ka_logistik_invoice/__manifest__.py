# -*- coding: utf-8 -*-
{
    'name': "LOG5 - Logistik Invoice",

    'summary': """
        Logistik invoice kebon agung""",

    'description': """
        Logistik invoice kebon agung
    """,

    'author': "PT. Kebon Agung",
    'website': "http://www.ptkebonagung.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Logistik',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'ka_logistik_sp'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/logistik_invoice.xml',
        'views/templates.xml',
    ],
}