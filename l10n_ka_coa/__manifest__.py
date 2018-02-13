# -*- coding: utf-8 -*-
{
    "name": "KA - Chart of Account",
     'description': """
    Chart of Account PT. Kebon Agung
     """,
	"version": "1.01",
    "author": "PT. Kebon Agung",
    "license": "AGPL-3",
    "category": "Localization",
    "website": "www.ptkebonagung.com",
    "depends": ["ka_account"],
    "data": [
        'data/l10n_ka_chart_data.xml',
        'data/account.account.template.csv',
        'data/ka_chart_template_data.xml',
        'data/ka_chart_template_data.yml',
        ],
    'installable': True,
}