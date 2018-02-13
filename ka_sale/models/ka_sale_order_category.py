from odoo import models, fields, api, _
from datetime import datetime
import json

class SaleOrderCategory(models.Model):
    _name ="ka_sale.order.category"
    _description = "Kategori Pejualan"
    _order = "sequence asc"

    name = fields.Char("Name")
    sequence = fields.Integer("Sequence")
    product_ids = fields.Many2many('product.product', 'ka_sale_order_categ_product_rel', 'sale_categ_id', 'product_id', string="Products")
    route_id = fields.Many2one("stock.location.route", string="Route", company_dependent=True)
    order_ids = fields.One2many('sale.order', 'so_categ_id', string='Sales Orders', readonly=True)
    need_contract = fields.Boolean('Need Contract')
    contract_template = fields.Many2one('ir.actions.report.xml', string='Kontrak SO')
    do_report_template = fields.Many2one('ir.actions.report.xml', string='Report DO')
    kanban_dashboard = fields.Text(compute='_kanban_dashboard')
    
    @api.one
    def _kanban_dashboard(self):
        self.kanban_dashboard = json.dumps(self.get_so_dashboard_datas())    
        
    @api.multi
    def action_new_so(self):
        ctx = self._context.copy()
        ctx.update({'active_id': self.id, 'active_so_categ_id': self.id})
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'context': ctx,
            'domain': [('so_categ_id', '=', self.id)],
        }
    
    @api.multi
    def get_so_action_so_category(self):
        for this in self:
            so_ids = [so.id for so in this.order_ids]
            context = dict(self.env.context or {})
            context['active_so_categ_id'] = this.id
            
            if len(so_ids) == 1:
                return {
                    'name': 'Sale Order',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_id' : so_ids[0],
                    'type': 'ir.actions.act_window',
                    'res_model': 'sale.order',
                    'context': context,
                    'target': 'current',  
                }
            else:
                return {
                    'name': 'Sale Orders',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'domain' : [('id','in',so_ids)],
                    'type': 'ir.actions.act_window',
                    'res_model': 'sale.order',
                    'context': context,
                    'target': 'current',  
                }
    
    @api.multi
    def get_so_dashboard_datas(self):
        res = list()
        for this in self:
            for so in this.order_ids:
                state = ''
                inv_state = ''
                if so.state == 'draft':
                    state = 'Quotation'
                elif so.state == 'sent':
                    state = 'Quotation Sent'
                elif so.state == 'sale':
                    state = 'Sale Order'
                elif so.state == 'done':
                    state = 'Locked'
                else:
                    state = 'Cancelled'
                    
                if so.invoice_status == 'upselling':
                    inv_state = 'Upselling Opportunity'
                elif so.invoice_status == 'invoiced':
                    inv_state = 'Fully Invoiced'
                elif so.invoice_status == 'to invoice':
                    inv_state = 'To Invoice'
                else:
                    inv_state = 'Nothing to Invoice'
                
                so_date = datetime.strftime(datetime.strptime(so.date_order, '%Y-%m-%d %H:%M:%S'), '%d-%m-%Y')
                vals = {
                        'id': so.id,
                        'no_so': so.name,
                        'tgl': so_date,
                        'partner': so.partner_id.name,
                        'state': state,
                        'state_inv': inv_state
                    }
                res.append(vals)
        return res