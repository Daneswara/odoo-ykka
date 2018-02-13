from odoo import models, fields, api, _
from openerp.addons.amount_to_text_id.amount_to_text import Terbilang

class account_invoice(models.Model):
    _inherit = "account.invoice"
    
    @api.model
    def default_get(self, fields):
        res = super(account_invoice,self).default_get(fields)
        active_model = self._context.get('active_model')
        if active_model == 'sale.order':
            sale_id = self._context.get('active_id')
            if sale_id:
                sale_order_id = self.env['sale.order'].browse(sale_id)
                res['agent_partner_id'] = sale_order_id.agent_partner_id.id or False
                res['sale_category_id'] = sale_order_id.so_categ_id.id
        return res
    
    agent_partner_id = fields.Many2one('res.partner', string="Agen")
    sale_category_id = fields.Many2one('ka_sale.order.category', 'Kategori Penjualan')
    
    def amount_to_text_id(self, amount):
        return Terbilang(amount) + " Rupiah"
    

class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"
    
    sale_order_number = fields.Char('Sales Order', readonly=True, compute='get_sale_order_number')
    
    @api.multi
    @api.depends('sale_line_ids')
    def get_sale_order_number(self):
        for this in self:
            res = ''
            for so_line in this.sale_line_ids:
                res += so_line.order_id.name + ' '
            this.sale_order_number = res