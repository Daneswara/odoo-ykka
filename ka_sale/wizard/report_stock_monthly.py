from openerp import models, fields, api, _
from datetime import datetime
from calendar import monthrange

@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()

class report_stock_monthly_wizard(models.TransientModel):
    _name = "report.stock.monthly.wizard"
    
    @api.model
    def default_get(self,fields):
        res = super(report_stock_monthly_wizard,self).default_get(fields)
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
        # default location
        location_factory = self.env.user.company_id.location_factory_id
        if location_factory:
            res['location_id'] = location_factory.id
        return res
    
    
    sale_category_id = fields.Many2one('ka_sale.order.category', 'Sale Category')
    location_id = fields.Many2one('stock.location', 'Location')
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
    def generate_report_stock_retail_monthly(self):
        report_obj = self.env['report']
        template = 'ka_sale.template_report_stock_retail_monthly'
        report = report_obj._get_report_from_name(template)
        domain = {
            'sale_category_id': self.sale_category_id.id,
            'location_id': self.location_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to
            }
        values = {
            'ids': self.ids,
            'model': report.model,
            'form': domain
            }
        return report_obj.get_action(self, template, data=values)
    

class report_stock_monthly_qweb(models.AbstractModel):
    _name = 'report.ka_sale.template_report_stock_retail_monthly'
    _template = 'ka_sale.template_report_stock_retail_monthly'
    
    def get_opening_stock(self, sale_category_id, location_id, date_from):
        source_uid = self.env.user.company_id.intercompany_user_id.id
        so_category = self.env['ka_sale.order.category'].browse(sale_category_id)
        product_ids = [product.id for product in so_category.product_ids]
        quants_today = self.env['stock.quant'].search([('product_id','in',product_ids),('location_id','=',location_id)])
        move_in_src = self.env['stock.move'].sudo(source_uid).search([('location_dest_id','=',location_id),
                                                                      ('product_id','in',product_ids),
                                                                      ('date','>=',date_from),
                                                                      ('picking_id.state','=','done')])
        move_out_src = self.env['stock.move'].sudo(source_uid).search([('location_id','=',location_id),
                                                                       ('product_id','in',product_ids),
                                                                       ('date','>=',date_from),
                                                                       ('picking_id.state','=','done')])
        stock_today = sum(quant.qty for quant in quants_today)
        stock_in = sum(move.product_uom_qty for move in move_in_src)
        stock_out = sum(move.product_uom_qty for move in move_out_src)
        return stock_today - stock_in + stock_out
        
 
    def get_stock_moves(self, sale_category_id, location_id, date_from, date_to):
        source_uid = self.env.user.company_id.intercompany_user_id.id
        so_category = self.env['ka_sale.order.category'].browse(sale_category_id)
        product_ids = [product.id for product in so_category.product_ids]
        stock_move_src = self.env['stock.move'].sudo(source_uid).search(['|',('location_id','=',location_id),
                                                                             ('location_dest_id','=',location_id),
                                                                             ('product_id','in',product_ids),
                                                                             ('date','>=',date_from),
                                                                             ('date','<=',date_to),
                                                                             ('picking_id.state','=','done')], order='date asc')
        res = []
        for move in stock_move_src:
            if move.location_dest_id.id == location_id and move.location_id.usage != 'customer':
                source_name = move.picking_id.picking_type_id.warehouse_id.name
                notes = 'Permintaan ' + source_name + ' (Gula Datang)'
                res.append({'date': datetime.strptime(move.picking_id.date_transfer, '%Y-%m-%d %H:%M:%S'),
                            'picking_number': move.picking_id.name,
                            'notes': notes,
                            'quantity_in': move.product_uom_qty,
                            'quantity_out': 0})
            elif move.location_id.id == location_id and move.location_dest_id.usage == 'customer':
                res.append({'date': datetime.strptime(move.picking_id.date_transfer, '%Y-%m-%d %H:%M:%S'),
                            'picking_number': move.picking_id.name,
                            'notes': move.picking_id.partner_id.name,
                            'quantity_in': 0,
                            'quantity_out': move.product_uom_qty})
        return res
 
    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        docargs = {
            'data': data['form'],
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
            'get_opening_stock': self.get_opening_stock,
            'get_stock_moves': self.get_stock_moves,
            }
        return report_obj.render(self._template, docargs)
     