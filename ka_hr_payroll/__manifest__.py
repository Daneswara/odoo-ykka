# -*- coding: utf-8 -*-
{
    'name': "SDM - Penggajian (Payroll)",

    'summary': """
        Modul penggajian karyawan""",

    'description': """
        Pengelolaan data penggajian karyawan
    """,

    'author': "PT. Kebon Agung",
    'website': "http://ptkebonagung.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Payroll',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_payroll', 'ka_hr_pegawai', 'ka_hr_attendance'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_company.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}