# -*- coding: utf-8 -*-
{
    'name': "ka_fingerspot",

    'summary': """
        Modul Mesin Absensi FingerSport""",

    'description': """
        Modul ini sebagai Gateway antara Mesin absensi FingerSport dan Easylink SDK
        Odoo<--->EasylinkSDK<--->FingerSpot Device
    """,

    'author': "PT. Kebon Agung",
    'website': "http://www.ptkebonagung.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/fingerspot_server.xml',
        'views/fingerspot_device.xml',
        'views/fingerspot_scanlog.xml',
        'views/fingerspot_user.xml',
        'views/fingerspot_action_log.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}