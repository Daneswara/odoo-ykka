from openerp import models, fields, api
from datetime import datetime
import pytz
from openerp.addons.amount_to_text_id.amount_to_text import Terbilang

class SaleContract(models.Model):
    _name = "sale.order.contract"
    _description = "Sale Contract for Current Type of Sales Product"

    delivery_number = fields.Char(string="Nomor DO")
    contract_date = fields.Date(string="Tanggal Kontrak")
    delivery_date = fields.Date(string="Tanggal DO")
    name = fields.Char(string="No. Contract")
    partner_id = fields.Many2one("res.partner", string="Pelanggan")
    operating_unit_id = fields.Many2one("res.partner", string="Unit/PG")
    quantity = fields.Float(string="Jumlah")
    product_uom = fields.Many2one('product.uom', 'Satuan Barang')
    order_id = fields.Many2one('sale.order', "Sale Order")
    currency_id = fields.Many2one("res.currency", related='order_id.currency_id', string="Currency", readonly=True, required=False)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
    partner_company_id = fields.Many2one('res.partner', related='company_id.partner_id', string='Local Partner')
    price_unit = fields.Monetary(string="Harga Unit")
    bank_name = fields.Many2one('res.partner.bank', 'Nama Bank')
    account_number = fields.Char(string="Nomor Rekening")
    down_payment_date = fields.Date(string="Tanggal Uang Muka")
    final_payment_date = fields.Date(string="Tanggal Pelunasan")
    date_expected = fields.Date(string="Jatuh Tempo")
    sale_date = fields.Date(string="Tanggal Pembelian")
    taun_produksi = fields.Selection(
                        [(str(num), str(num)) 
                        for num in range((datetime.now().year),(datetime.now().year)-10,-1)]
                    ,'Tahun Produksi')
    note_pengambilan = fields.Text(string="Catatan Pengambilan")
    ttd_customer = fields.Many2one("res.partner", string="Tanda tangan")
    
    @api.onchange('bank_name')
    def onchange_bank_name(self):
        self.account_number = self.bank_name.acc_number
    
    def amount_to_text_id(self, amount):
        return Terbilang(amount)
    
    @api.multi
    def get_kontrak_template(self):
        for this in self:
            report_name = this.order_id.so_categ_id.contract_template.report_name
            report_obj = this.env['report']
            report = report_obj._get_report_from_name(report_name)
            model = report.model
            data = self.read()[0]
            datas = {'ids': [this.id],
                     'model': model,
                     'form': data,
                     'context':self._context}
            return {
                'type': 'ir.actions.report.xml',
                'report_name': report_name,
                'datas': datas,
            }
        