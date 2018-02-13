# -*- coding: utf-8 -*-
{
    'name': "KA Base Setting",

    'summary': """
        Modul Dasar untuk PT. Kebon Agung""",

    'description': """
        Customize module :
        
        1. res.company :
            - add field intercompany_user_id  --> sebagai user yang secara otomatis melakukan R/K
            - add field code  --> code perusahaan
        2. res.partner :
            - Add fields is_operating_unit --> untuk mengakomodir jurnal R/K
    """,

    'author': "PT. Kebon Agung",
    'website': "http://www.ptkebonagung.com",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'views/res_user_view.xml',
        'views/ka_base_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}