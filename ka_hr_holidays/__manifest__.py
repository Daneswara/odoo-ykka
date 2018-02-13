# -*- coding: utf-8 -*-
{
    'name': "SDM - Absensi",

    'summary': """
        Absensi ketidakhadiran pegawai""",

    'description': """
        Pengelolaan data absensi ketidakhadiran pegawai baik cuti, ijin, dll.
        Extends dari hr_holidays
    """,

    'author': "PT. Kebon Agung",
    'website': "http://ptkebonagung.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'ka_hr_pegawai',
        'hr_holidays',
        'ka_report_layout',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'reports/employee_holidays.xml',
        'reports/employee_dinas.xml',
        
        'wizards/holidays_config.xml',

        'views/menu.xml',
        'views/holidays_public.xml',
        'views/holidays_group.xml',
        'views/holidays_status.xml',
        'views/employee_holidays.xml',
        'views/employee_holidays_general.xml',
        'views/hr_employee.xml',
        'views/res_company.xml',
        'views/holidays_afkoop.xml',

        'data/ir_cron_employee_holidays_allocation.xml',
        'data/template_mail_cuti_approval.xml',
        'data/template_mail_cuti_approved.xml',
        'data/template_mail_cuti_refused.xml',
        'data/template_mail_cuti_allocation.xml',
        'data/ir_sequence.xml',

        'helpers/cleaning_field.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}