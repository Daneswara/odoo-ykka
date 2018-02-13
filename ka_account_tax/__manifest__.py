# -*- coding: utf-8 -*-
{
    "name": "KA Account Tax",
     'description': """
Untuk mongakomodir Aplikasi Perpajakan 
- PPN 
- Butki Potong PPh

    """,
    "version": "1.01",
    "author": "PT. Kebon Agung",
    "license": "AGPL-3",
    "category": "Account",
    "website": "www.ptkebonagung.com",
    "depends": ["ka_account","ka_purchase"],
    "data": [
#        "security/account_tax_security.xml",
        "security/ir.model.access.csv",
        "report/ka_account_pph_buktipotong_envelope.xml",
        "views/ka_account_tax_view.xml",
        "views/ka_account_payment_view.xml",
        ],
    'installable': True,
}