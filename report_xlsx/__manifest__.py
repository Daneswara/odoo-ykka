{
    'name': "Base report xlsx",
    'version': '0.2',
    'category': 'Reporting',
    'summary': """
        Simple upgradation of v9 OCA module 'report_xlsx' to v10""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',
    'license': 'AGPL-3',
    'external_dependencies': {'python': ['xlsxwriter']},
    'depends': [
        'base',
    ],
    'installable': True,
    'auto_install': False,
}
