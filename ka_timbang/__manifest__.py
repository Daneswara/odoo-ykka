# -*- coding: utf-8 -*-
{
    "name": "KA Timbangan",
     'description': """
Module Timbangan yang di sesuaikan dengan kebutuhan PT. Kebon Agung.

    """,
    "version": "1.01",
    "author": "PT. Kebon Agung",
    "license": "AGPL-3",
    "category": "Timbangan",
    "website": "www.ptkebonagung.com",
    "depends": ["ka_base", "stock"],
    "data": [
        "security/timbang_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "views/timbang_view.xml"
        ],
    'installable': True,
}