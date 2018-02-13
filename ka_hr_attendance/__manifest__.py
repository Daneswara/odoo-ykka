# -*- coding: utf-8 -*-
{
    'name': "SDM - Presensi",

    'summary': """
        Presensi kehadiran pegawai""",

    'description': """
        Pengelolaan data presensi kehadiran pegawai.
        Extends dari hr_attendance
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
        'ka_fingerspot',
        'hr_attendance',
        'ka_hr_holidays',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        
        'reports/weekly_report.xml',
        'reports/monthly_report.xml',

        'wizards/attendance_config.xml',
        'wizards/fingerspot_attendance_import.xml',
        'wizards/monthly_report.xml',

        'views/menu.xml',
        'views/employee_attendance.xml',
        'views/menu.xml',
        'views/shift.xml',
        'views/group.xml',
        'views/hr_employee.xml',
        'views/attendance_report_weekly.xml',
        'views/res_company.xml',

        'data/ir_cron_fingerspot_scan.xml',
        'data/ir_cron_weekly_report_mail.xml',
        'data/template_mail_no_check_in.xml',
        'data/template_mail_no_check_out.xml',
        'data/template_mail_weekly_report.xml',

        'helpers/cleaning_db.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}