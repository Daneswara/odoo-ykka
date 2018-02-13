from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError
from datetime import datetime
import math
from openerp.addons.amount_to_text_id.amount_to_text import Terbilang

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    so_categ_id = fields.Many2one('ka_sale.order.category', string='Kategori Penjualan')
    agent_partner_id = fields.Many2one('res.partner', string="Agen", domain=[('company_type', '=', 'person')])
    delivery_number = fields.Char('No. Kirim')
    timbangan_id = fields.Many2one('ka_timbang.material', 'No. Timbangan')

    def jum_keluar_gula(self):
        order = False
        for line in self.sale_id.order_line:
            order = line.product_uom_qty / line.product_id.production_uom_id.factor_inv
            break
        return order
    
    def get_netto_karung(self):
        netto = False
        for line in self.sale_id.order_line:
            netto = self.timbangan_id.weight_net / line.product_id.production_package_uom_id.factor_inv
            break
        return netto
    
    def get_taun_produksi(self):
        source_uid  =  self.env.user.company_id.intercompany_user_id.id
        so = self.sale_id
        if self.sale_id.source_so_id:
            so = self.env['sale.order'].sudo(source_uid).search([('id','=', self.sale_id.source_so_id.id)])
        elif self.sale_id.dest_so_id:
            so = self.env['sale.order'].sudo(source_uid).search([('id','=', self.sale_id.dest_so_id.id)])
            
        kontrak = self.env['sale.order.contract'].search([('order_id','=',so.id)])
        print('----------------------------------------- >>>>>>>>>>', self.sale_id.id)
        print('----------------------------------------- >>>>>>>>>>', kontrak.taun_produksi)
        return kontrak.taun_produksi
    
    def amount_to_text_id(self, amount):
        return Terbilang(amount) + " Karung"
    
    @api.multi
    def get_max_array(self):
        for this in self:
            count_moves = float(len(this.move_lines))
            count_moves = int(math.ceil(count_moves/5))
            this.max_array = count_moves
    
    max_array = fields.Integer('Max Array', compute='get_max_array')

    def get_rows(self):
        count = 1
        rows = list()
        cols = list()
        for item in self.move_lines:
            vals = {'no': count,
                    'name': item.product_id.name,
                    'code': item.product_id.default_code,
                    'qty_dos': item.product_uom_qty*item.product_uom.factor_inv,
                    'qty_kg': item.product_uom_qty
                    }
            if count == 10:
                cols.append(vals)
                rows.append(cols)
                cols = list()
                count = 1
            else:
                cols.append(vals)
                count += 1
        if count > 0:
            for i in range(6-count):
                vals = {'no': count,
                        'name': '',
                        'code': '',
                        'qty_dos': '',
                        'qty_kg': ''
                        }
                cols.append(vals)
            rows.append(cols)
        return rows

    @api.multi
    def print_bukti_pengeluaran(self):
        for this in self:
            report_name = this.so_categ_id.do_report_template.report_name
            report_name_str = str(report_name)
            active_id = self._context.get('active_id',False)
            report_obj = this.env['report']
            report = report_obj._get_report_from_name(report_name_str)
            model = report.model
            data = self.read()[0]
            datas = {'ids': [active_id],
                     'model': model,
                     'form': data,
                     'context':self._context}
            return {
                'type': 'ir.actions.report.xml',
                'report_name': report_name_str,
                'datas': datas,
            }

