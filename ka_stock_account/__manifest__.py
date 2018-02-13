{
    "name": "KA Stock Account",
    'description': """
Module stock_account disesuaikan dengan kebutuhan PT. KA :
- Buat Pickting Type baru --> Pemeriksaan(WH/Input > WH/Stock) dan Bon Pemakaian Material (WH/Stock > Lokasi pemakai barang)
- Tambah field analytic pada saat Bon Pemakaian barang
    """,
    "version": "1.01",
    "author": "PT. Kebon Agung",
    "license": "AGPL-3",
    "category": "Purchases",
    "website": "www.ptkebonagung.com",
    "depends": ["analytic",
                "stock_account",
                "ka_stock",
                "stock",
                "ka_purchase"],
    "data": [
#         "data/ir_sequence.xml",
        "report/report_stock_product_receive.xml",
        "report/report_transaction_usage.xml",
        "report/tmpl_report_transaction_usage.xml",
        "report/report_stock_product_return.xml",
        "wizard/stock_picking_return_view.xml",
        "views/account_config_view.xml",
        "views/res_partner_view.xml",
        "views/stock_view.xml",
        "views/stock_move_view.xml",
        ],
    'installable': True,
}