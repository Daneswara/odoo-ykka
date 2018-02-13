# -*- coding: utf-8 -*-
{
    'name': "LOG3 - KA Logistik SPM",

    'summary': """
        Permintaan Material""",

    'description': """
        LOG3 Permintaan Material
        Modul ini digunakan dalam proses pembelian barang
        SPM(Surat Permintaan Material
    """,

    'author': "PT. Kebon Agung",
    'website': "http://ptkebonagung.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Logistik',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['ka_logistik_master', 
                'ka_logistik_rab', 
                'ka_logistik_pkrat',
                'hr', 
                'ka_report_layout'],

    # always loaded
    'data': [
        'security/logistik_spm.xml',
        'security/ir.model.access.csv',
        'wizard/logistik_spm_merge_dbf_view.xml',
        'wizard/logistik_spm_line_approve.xml',
        'wizard/logistik_spm_pengajuan_direksi.xml',
        'wizard/logistik_spm_nomor.xml',
        'wizard/logistik_spm_approve.xml',
        'wizard/logistik_realisasi_spm.xml',
        'wizard/logistik_spm_cancel.xml',
        'wizard/logistik_edit_jenis_pengadaan_view.xml',
	    'views/logistik_spm_templates.xml',
        'views/logistik_pengajuan_spm.xml',
        'views/logistik_spm.xml',
        'views/department.xml',
		'views/product_request_view.xml',
        # 'views/purchase_view.xml',
        'views/logistik_spm_config_view.xml',
        'report/logistik_spm.xml',
        'data/logistik_spm.xml',
        'data/mail_template.xml'
    ],
}