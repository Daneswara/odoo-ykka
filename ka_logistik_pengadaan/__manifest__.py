# -*- coding: utf-8 -*-
{
    'name': "KA Logistik - Pengadaan Barang",

    'summary': """
        KA Logistik - Pengadaan Barang""",

    'description': """
        Modul ini digunakan dalam proses pembelian barang SPM Direksi\n
        Penggolongan SPM\n
        SPP(Surat Permintann Penawaran)\n 
        Tender
    """,

    'author': "PT. Kebonagung",
    'website': "http://ptkebonagung.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Logistik',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 
                'ka_report_layout',
                'ka_purchase', 
                'ka_hr_pegawai',
                'ka_logistik_spm'],

    # always loaded
    'data': [
        'security/logistik_pengadaan.xml',
        'security/ir.model.access.csv',
        'wizard/logistik_spm_penggolongan.xml',
        'wizard/logistik_tender_rekanan.xml',
        'wizard/logistik_tender_cancel.xml',
        'views/logistik_spm.xml',
        'views/logistik_spp.xml',
        'views/logistik_tender.xml',
        'views/logistik_sp.xml',
        'views/templates.xml',
        'views/purchase_view.xml',
        'views/stock_move_view.xml',
        'report/spp.xml',
        'report/spp_result.xml',
        'report/tender_spp.xml',
        'report/tender_result.xml',
    ],
}