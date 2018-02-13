# -*- coding: utf-8 -*-
{
    'name': "KA - Tanaman",

    'summary': """
        Modul Tanaman PT. Kebonagung""",

    'description': """
        Modul Tanaman PT. Kebonagung
    """,

    'author': "PT. Kebonagung",
    'website': "http://www.ptkebonagung.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'ka_logistik_master',
        'ka_base_wilayah',
        'ka_account',
        'ka_hr_pegawai',
        'ka_manufacture',
    ],

    # always loaded
    'data': [
        'report/report_estimasi_view.xml',
        'report/report_hasil_taksasi_view.xml',
        'report/wizard_hasil_taksasi.xml',
        'wizard/upload_gps_file_wizard.xml',
        'wizard/area_intersect_view.xml',
        'wizard/wizard_print_polygon.xml',
        'views/assets.xml',
        # 'views/ts_category.xml',
        # 'views/ts_category_cost.xml',
        'views/area_taksasi_periode.xml',
        'views/periode.xml',
        'views/area_rehabilitation.xml',
        'views/area.xml',
        'views/area_agronomi.xml',
        'views/kud.xml',
        'views/ts_contract.xml',
        'views/hasil_taksasi.xml',
        'views/register.xml',
        'views/mtt.xml',
        'views/area_taksasi.xml',
        'views/base_wilayah.xml',
        'views/varietas.xml',
        'views/farmer.xml',
        'views/intesifikasi.xml',
        'views/credit_category.xml',
        'views/credit_farmer.xml',
        'views/credit_kud.xml',
        'views/area_sampling_line.xml',
        'views/area_sampling_view.xml',
        'views/zona_rehabilitasi.xml',
        'views/config.xml',
        'security/tanaman_security.xml',
        'security/ir.model.access.csv',
        'views/menu.xml',
    ],

    'qweb': ['static/src/xml/*.xml'],
}