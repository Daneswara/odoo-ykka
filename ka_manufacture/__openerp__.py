# -*- coding: utf-8 -*-
{
    "name": "KA Manufacture",
     'description': """
Module Produksi yang di sesuaikan dengan kebutuhan PT. Kebon Agung.

    """,
    "version": "1.01",
    "author": "PT. Kebon Agung",
    "license": "AGPL-3",
    "category": "Manufacturing",
    "website": "www.ptkebonagung.com",
    "depends": ["stock", "ka_account"],
    "data": [
        "security/ir.model.access.csv",
        "security/stock_security.xml",
        "views/ka_manufacture_session_view.xml",
        "views/ka_manufacture_daily_view.xml",
        "views/ka_manufacture_closing_period_view.xml"
        ],
    'installable': True,
}