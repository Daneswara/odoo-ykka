from openerp import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from calendar import monthrange

@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()

class report_penjualan_gula_retail(models.TransientModel):
    _name = "report.penjualan.gula.retail.wiz"
    
    @api.model
    def default_get(self,fields):
        res = super(report_penjualan_gula_retail,self).default_get(fields)
        # default date
        year = datetime.now().year
        month = datetime.now().month
        last_day = monthrange(year, month)[1]
        res['date_from'] = datetime.strftime(datetime(year, month, 1), '%Y-%m-%d')
        res['date_to'] = datetime.strftime(datetime(year, month, last_day), '%Y-%m-%d')
        # default category
        product_retail = self.env.user.company_id.product_sugar_retail_id
        if product_retail:
            sale_category_src = self.env['ka_sale.order.category'].search([('product_ids','=',product_retail.id)],limit=1)
            if sale_category_src:
                res['sale_category_id'] = sale_category_src.id
        
        return res
    
    
    sale_category_id = fields.Many2one('ka_sale.order.category', 'Sale Category')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    lang = fields.Selection(_lang_get, string='Language', default=lambda self: self.env.ref('base.lang_id').code,
                            help="If the selected language is loaded in the system, all documents related to "
                                 "this contact will be printed in this language. If not, it will be English.")
    
    @api.onchange('date_from')
    def onchange_date_from(self):
        if self.date_from:
            date_from = datetime.strptime(self.date_from, '%Y-%m-%d')
            year = date_from.year
            month = date_from.month
            last_day = monthrange(year, month)[1]
            self.date_to = datetime.strftime(datetime(year, month, last_day), '%Y-%m-%d')
    
    
    @api.multi
    def generate_report_penjualan_gula_retail(self):
        if self.date_from > self.date_to:
            raise UserError('Date To should be greater than Date From')
        
        report_obj = self.env['report']
        template = 'ka_sale.template_report_penjualan_gula_retail'
        report = report_obj._get_report_from_name(template)
        domain = {
            'date_from': self.date_from,
            'date_to' : self.date_to,
            }
        values = {
            'ids': self.ids,
            'model': report.model,
            'form': domain
            }
        return report_obj.get_action(self, template, data=values)

class report_penjualan_gula_retail_qweb(models.AbstractModel):
    _name = 'report.ka_sale.template_report_penjualan_gula_retail'
    _template = 'ka_sale.template_report_penjualan_gula_retail'
    
    def get_sale_order_lines(self, date_from, date_to, sale_category_id):
        
        start_date = datetime.strptime(date_from, '%Y-%m-%d')
        start_date = start_date.replace(hour=00, minute=00, second=00)
        start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        
        end_date = datetime.strptime(date_to, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
        end_date = datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        sale_order_lines = self.env['sale.order.line'].search([('order_id.date_order','<=', end_date),
                                                               ('order_id.date_order','>=', start_date),
                                                               ('state','not in',('draft','cancel')),
                                                               ('order_id.so_categ_id','=', sale_category_id.id)])

        res = list()
        for i in sale_order_lines:
            res.append(i)
        return res

    def get_picking_id(self, order_line):
        source_uid = self.env.user.company_id.intercompany_user_id.id
        res = list()
        if order_line.order_id.saleorder_type == 'rkout':
            for picking in order_line.order_id.sudo(source_uid).dest_so_id.picking_ids:
                if picking not in res and picking.state == 'done':
                    for pack in picking.pack_operation_product_ids:
                        if pack.product_id == order_line.product_id:
                            res.append(picking)
        else:
            for picking in order_line.order_id.picking_ids:
                if picking not in res and picking.state == 'done':
                    for pack in picking.pack_operation_product_ids:
                        if pack.product_id == order_line.product_id:
                            res.append(picking)
        return res
    
    def get_invoice_id(self, order_line):
        res = list()
        for invoice in order_line.order_id.invoice_ids:
            if invoice not in res and invoice.state != 'draft':
                for line in invoice.invoice_line_ids:
                    if line.product_id == order_line.product_id:
                        res.append(invoice)
        return res
            
    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        docargs = {
            'data': data['form'],
            'get_sale_order_lines': self.get_sale_order_lines,
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
            'get_picking_id': self.get_picking_id,
            'get_invoice_id':self.get_invoice_id,
            }
        return report_obj.render(self._template, docargs)
