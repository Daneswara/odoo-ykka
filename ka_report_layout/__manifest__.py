# -*- coding: utf-8 -*-
{
    'name': "KA Report Layout",

    'summary': """
        Modify report layout""",

    'description': """
        Modify report layout
    """,

    'author': "PT. Kebon Agung",
    'website': "http://www.ptkebonagung.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Report',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['report'],

    # always loaded
    'data': [
        'report/external_layout_header.xml',
        'report/external_layout_footer.xml',
        'report/ka_external_layout_header.xml',
        'report/ka_external_layout.xml',
        'report/ka_external_layout_logo_only.xml',
        'report/external_layout_header_logo_only.xml',
        'report/ka_layout_no_header.xml',
        'report/ka_layout_header_logistik.xml',
        'report/ka_layout_header_logistik_2.xml',
        'report/ka_layout_header_tandaterima_logistik.xml',
        'report/ka_layout_footer_logistik.xml',
        'report/layout_header_internal.xml',
        'report/paper_format.xml',
    ],

    'images': [
        'static/src/img/logo-ptkebonagung.png',
        'static/src/img/icon-kebonagung.png',
    ],

    'css': [
        'static/src/css/style.css',
    ],
}