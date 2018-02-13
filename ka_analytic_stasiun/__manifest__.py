# -*- coding: utf-8 -*-
{
    'name': "Analytic Account Stasiun",

    'summary': """
        Analytic Account Stasiun & Link to department""",

    'description': """
    """,

    'author': "PT. Kebon Agung",
    'website': "http://ptkebonagung.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Account',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'analytic'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
		'security/stasiun_security.xml',
        'views/analytic.xml',
    ],
}