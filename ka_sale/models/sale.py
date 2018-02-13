import time
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    READONLY_STATES = {
        'sale': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }
    operating_unit_id = fields.Many2one('res.partner', string="Unit/PG", states=READONLY_STATES, domain=[('is_operating_unit', '=', True)])
    source_partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)
    source_so_id = fields.Many2one('sale.order', 'Source SO', copy=False)
    dest_so_id = fields.Many2one('sale.order', 'Destination SO', copy=False)
    saleorder_type = fields.Selection([
                        ('rkout', 'SO Untuk Unit'), 
                        ('rkin', 'SO Dari Unit'), 
                        ('lokal', 'SO Local')
                        ],string="Jenis SO", default="lokal", readonly=True, copy=False)
    sale_contract_id = fields.Many2one('sale.order.contract', string='Contract', copy=False)
    timbangan_ids = fields.One2many('ka_timbang.material', 'no_do', string='Timbangan associated to this sale')
    timbangan_count = fields.Integer(string='Timbangan', compute='_compute_timbangan_ids')
    invisible_button_invoice = fields.Boolean('Invisible Button Invoice', compute='get_invisible_button_invoice', copy=False)
    so_categ_id = fields.Many2one('ka_sale.order.category', string='Kategori Penjualan')
    need_contract= fields.Boolean('Need Contract', related='so_categ_id.need_contract')
    product_ids = fields.Many2many(comodel_name='product.product',
                         relation='sale_order_product_rel',
                         column1='order_id',
                         column2='product_id', string="Customer Products")
    agent_partner_id = fields.Many2one('res.partner', string="Agen", domain=[('company_type', '=', 'person')])
    

    @api.multi
    @api.depends('state','invoice_status','sale_contract_id')
    def get_invisible_button_invoice(self):
        for this in self:
            this.invisible_button_invoice = (this.state in ('draft','cancel','done') or this.invoice_status != 'to invoice' or (this.need_contract and not this.sale_contract_id))
    
    @api.multi
    def _compute_timbangan_ids(self):
        for order in self:
            order.timbangan_count = len(order.timbangan_ids)
            
    @api.multi
    def action_view_timbangan(self):
        action = self.env.ref('ka_timbang.timbang_material_menu_action').read()[0]
        timbangan = self.mapped('timbangan_ids')
        if len(timbangan) > 1:
            action['domain'] = [('id', 'in', timbangan.ids)]
        elif timbangan:
            action['views'] = [(self.env.ref('ka_timbang.timbang_material_form_view').id, 'form')]
            action['res_id'] = timbangan.id
        return action        
    
    def action_view_contract(self):
        return {
            'name': 'Sales Contract',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.sale_contract_id.id,
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.contract',
            'target': 'current',
        }
    
    def get_date(self, date):
        m = ''
        thedate = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        month = thedate.strftime("%B")
        if month == 'January':
            m = 'Januari'
        elif month == 'February':
            m = 'Februari'
        elif month == 'March':
            m = 'Maret'
        elif month == 'May':
            m = 'Mei'
        elif month == 'June':
            m = 'Juni'
        elif month == 'July':
            m = 'Juli'
        elif month == 'August':
            m = 'Agustus'
        elif month == 'October':
            m = 'Oktober'
        elif month == 'December':
            m = 'Desember'
        else:
            m=month
        d = thedate.strftime("%-d")
        y = thedate.strftime("%Y")
        res = d + " " + m + " " + y
        return res
             
    @api.multi    
    def create_sale_contract(self):
        for this in self:
            for line in this.order_line:
                bank_src = self.env['res.partner.bank'].search([('partner_id','=',this.company_id.partner_id.id)], order='priority asc, id desc', limit=1)
                req_date = '...'
                if this.requested_date:
                    req_date = self.get_date(this.requested_date)
                data = {
                    'name' : this.name,
                    'partner_id' : this.partner_id.id,
                    'operating_unit_id' : this.operating_unit_id.id,
                    'quantity' : line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'price_unit' :line.price_unit,
                    'date_expected' : this.requested_date,
                    'sale_date' : this.date_order,
                    'order_id' : this.id,
                    'contract_date': this.date_order,
                    'bank_name': bank_src.id,
                    'account_number': bank_src.acc_number,
                    'note_pengambilan':'Pengambilan gula paling lambat tanggal ' + req_date + ' dan apabila melampaui maka dikenakan biaya penyimpanan secara progresif sesuai ketentuan perusahaan.'
                }
                res_id = self.env['sale.order.contract'].create(data)
                this.sale_contract_id = res_id.id
                
                return {
                    'name': 'Sales Contract',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_id': res_id.id,
                    'type': 'ir.actions.act_window',
                    'res_model': 'sale.order.contract',
                    'target': 'current',
                }
    
    @api.one
    def copy_saleorder_to_ou(self):
        source_uid = self.env.user.company_id.intercompany_user_id.id
        ou_company = self.sudo(source_uid).operating_unit_id.get_company_ref()[0]
        
        default = {
            'name': self.name,
            'date_order': self.date_order,
            'requested_date': self.requested_date,
            'confirmation_date': self.confirmation_date,
            'commitment_date': self.commitment_date,
            'effective_date': self.effective_date,
            'company_id': ou_company.id,
            'source_partner_id':self.partner_id.id,
            'source_so_id':self.id,            
            'partner_id': self.company_id.partner_id.id,
            'partner_invoice_id': self.company_id.partner_id.id,
            'saleorder_type': 'rkin',
            'warehouse_id': self.env['stock.warehouse'].sudo(source_uid).search([('company_id','=',ou_company.id)], limit=1).id,
            'order_line': None,
        }
        copy_saleorder = self.sudo(source_uid).copy(default=default)
        self.dest_so_id = copy_saleorder.id
        product_dp = self.env['ir.values'].get_default('sale.config.settings', 'deposit_product_id_setting')
        
        for line in self.order_line:
            if line.product_id.id <> product_dp:
                default_line = {
                    'order_id': copy_saleorder.id,
                    'source_saleorder_line_id': line.id,
                    'company_id': ou_company.id,
                    'route_id': self.so_categ_id.sudo(ou_company.internal_user_id.id).with_context(company_id=ou_company.id).route_id.id,
                    'invoice_lines': []
                }
   
                copy_line = line.sudo(source_uid).copy(default=default_line)
                line.dest_saleorder_line_id = copy_line.id
                
        copy_saleorder.sudo(source_uid).action_confirm()
        for picking in self.dest_so_id.sudo(source_uid).picking_ids:
            picking.sudo(source_uid).write({'so_categ_id': self.so_categ_id.id})
        return copy_saleorder
                
    @api.multi
    def action_confirm(self):
        for saleorder in self:
            if saleorder.operating_unit_id.id <> saleorder.company_id.partner_id.id:
                self.saleorder_type = 'rkout'
            saleorder.state = 'sale'
            if not saleorder.confirmation_date:
                saleorder.confirmation_date = fields.Datetime.now()
            if self.env.context.get('send_email'):
                self.force_quotation_send()
            
            if self.operating_unit_id.id == self.company_id.partner_id.id:
                saleorder.order_line._action_procurement_create()
                for picking in self.picking_ids:
                    picking.write({'so_categ_id': self.so_categ_id.id, 
                                   'agent_partner_id': self.agent_partner_id.id})
                
        if self.env['ir.values'].get_default('sale.config.settings', 'auto_done_setting'):
            self.action_done()
        return True
    
    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))
        # add condition context internal user from SO
        account_id = self.partner_invoice_id.property_account_receivable_id.id
        internal_user = self._context.get('internal_user',False)
        if internal_user:
            account_id = self.sudo(internal_user).partner_invoice_id.property_account_receivable_id.id
        
        invoice_vals = {
            'name': self.client_order_ref or '',
            'origin': self.name,
            'type': 'out_invoice',
            'account_id': account_id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id
        }
        if self.source_partner_id:
            invoice_vals['source_partner_id'] = self.source_partner_id.id
        return invoice_vals
    
    @api.multi
    def action_create_so_factory(self):
        source_uid = self.env.user.company_id.intercompany_user_id.id
        ou_company = self.sudo(source_uid).operating_unit_id.get_company_ref()[0]
        for saleorder in self:
            if saleorder.operating_unit_id.id <> saleorder.company_id.partner_id.id:
                saleorder.copy_saleorder_to_ou()
                saleorder_result = saleorder.sudo(source_uid).with_context(company_id=ou_company.id).dest_so_id
                if saleorder_result:
                    saleorder_result.with_context(company_id=ou_company.id, internal_user=ou_company.internal_user_id.id).action_invoice_create(final=True)
                    for invoice in saleorder_result.invoice_ids: 
                        if invoice.state == 'draft' and invoice.company_id.id == ou_company.id:
                            invoice.sudo(ou_company.internal_user_id.id).with_context(company_id=ou_company.id).action_invoice_open()
    
    @api.model
    def default_get(self, fields):
        res = super(SaleOrder,self).default_get(fields)
        if self._context.get('active_so_categ_id'):
            res['so_categ_id'] = self._context.get('active_so_categ_id')
        return res
    
    @api.onchange('partner_id')
    def onchange_partner_id_so_categ(self):
        if self.partner_id and not self._context.get('active_so_categ_id'):
            so_categ_id = False
            categ_ids = []
            for categ in self.partner_id.sale_product_ids:
                so_categ_id = categ.id
                categ_ids.append(so_categ_id)
            self.so_categ_id = so_categ_id
            return {'domain': {'so_categ_id': [('id','in',categ_ids)]}}
    
    @api.onchange('partner_id')
    def onchange_partner_id_product_ids(self):
        if self.partner_id:
            ids = []
            for category in self.partner_id.sale_product_ids:
                for product in category.product_ids:
                    ids.append(product.id)
            self.product_ids = ids
     
    @api.onchange('so_categ_id')
    def onchange_sale_category(self):
        if self.so_categ_id:
            product_id = False
            for product in self.so_categ_id.product_ids:
                product_id = product
                break
            order_line_vals = {'name': product_id.display_name,
                               'product_id': product_id.id,
                               'product_uom_qty': 1,
                               'product_uom': product_id.uom_id.id,
                               'price_unit': product_id.lst_price,
                               'route_id': self.so_categ_id.route_id.id or False}
            self.order_line = [(0,0,order_line_vals)]
            
            active_so_categ_id = self._context.get('active_so_categ_id')
            if active_so_categ_id:
                return {'domain': {'partner_id': [('sale_product_ids','=',active_so_categ_id)], 'so_categ_id': [('id','=',active_so_categ_id)]}}
    
        
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    source_saleorder_line_id = fields.Many2one('sale.order.line', string="Source Sale Order Line", copy=False)
    dest_saleorder_line_id = fields.Many2one('sale.order.line', string="Destination Sale Order Line", copy=False)
    qty_delivered_unit = fields.Float('Delivered', compute='compute_qty_delivered_unit', readonly=True)
    check_qty = fields.Boolean(string='Check Qty', compute='_check_qty')
    line_created = fields.Boolean(string='Line Created')
    product_ids_line = fields.Many2many("product.product", related='order_id.product_ids', string="Customer Products")

    @api.model
    def default_get(self, fields):
        res = super(SaleOrderLine,self).default_get(fields)
        so_categ_id = self._context.get('so_categ_id')
        product_ids = self._context.get('product_ids')
        if so_categ_id:
            res['route_id'] = self.env['ka_sale.order.category'].browse(so_categ_id).route_id.id
        if product_ids:
            res['product_ids_line'] = product_ids[0][2]
        return res
    
    @api.multi
    @api.depends('dest_saleorder_line_id.qty_delivered','qty_delivered')
    def compute_qty_delivered_unit(self):
        for this in self:
            res = 0.0
            intercompany_user = this.order_id.company_id.intercompany_user_id.id
            if this.sudo(intercompany_user).dest_saleorder_line_id:
                res = this.sudo(intercompany_user).dest_saleorder_line_id.qty_delivered
            else:
                res = this.qty_delivered
            this.qty_delivered_unit = res
            
    @api.one
    @api.depends('qty_delivered','product_uom_qty')
    def _check_qty(self):
        if self.qty_delivered <= self.product_uom_qty:
            check_qty = False
        else:
            check_qty = True
        self.check_qty = check_qty
    
    @api.multi
    def adjust_qty(self):
        for this in self:
            if this.order_id.saleorder_type == 'lokal':
                upselling_qty = this.qty_delivered - this.product_uom_qty
                sale_order_line = self.env['sale.order.line']
                
                data_entry = {
                    'product_id' : this.product_id.id,
                    'name' : 'Kelebihan Pengambilan' +' '+ this.product_id.display_name,
                    'product_uom_qty': upselling_qty,
                    'qty_delivered': upselling_qty,
                    'analytic_tag_ids': this.analytic_tag_ids.id,
                    'price_unit': this.price_unit,
                    'tax_id' : False,
                    'order_id' : this.order_id.id,
                    }
                
                sale_order_line.create(data_entry)
                
                vals = {'qty_delivered': this.product_uom_qty}
                this.write(vals)
                
            elif this.order_id.saleorder_type == 'rkin':
                source_uid = self.env.user.company_id.intercompany_user_id.id
                upselling_qty = this.qty_delivered - this.product_uom_qty
                sale_order_line = self.env['sale.order.line']
                
                data_entry = {
                    'product_id' : this.product_id.id,
                    'name' : 'Kelebihan Pengambilan '+ this.product_id.display_name,
                    'product_uom_qty': upselling_qty,
                    'qty_delivered': upselling_qty,
                    'analytic_tag_ids': this.analytic_tag_ids.id,
                    'price_unit': this.price_unit,
                    'order_id' : this.order_id.sudo(source_uid).source_so_id.id,
                    'tax_id' : False,
                    }
                
                sale_order_line.sudo(source_uid).create(data_entry)
                vals = {'line_created' : True}
                this.write(vals)
                         
        return True
    
    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity')
    def _get_invoice_qty(self):
        for line in self:
            super(SaleOrderLine, line)._get_invoice_qty()
            sol_id = line.source_saleorder_line_id
            if sol_id:
                self._cr.execute("UPDATE sale_order_line SET qty_delivered = %s WHERE id=%s", (line.qty_invoiced, sol_id.id))

    @api.onchange('product_uom')
    def product_uom_change(self):
        if not self.product_uom:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date_order=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.price_unit = self.env['account.tax']._fix_tax_included_price(self._get_display_price(product), product.taxes_id, self.tax_id)
             
    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        #check SO local or not
        if self.product_id.type == 'product' and self.order_id.operating_unit_id.id != self.order_id.company_id.partner_id.id:
            account = self.order_id.operating_unit_id.property_account_receivable_id
        # add condition context internal user from SO
        internal_user_ctx = self._context.get('internal_user',False)
        if internal_user_ctx:
            account = self.sudo(internal_user_ctx).product_id.property_account_income_id or self.sudo(internal_user_ctx).product_id.categ_id.property_account_income_categ_id
        
        if not account:
            raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'layout_category_id': self.layout_category_id and self.layout_category_id.id or False,
            'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.project_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
        }
        return res

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        if not self.product_id or not self.product_uom_qty or not self.product_uom or self.order_id.operating_unit_id.id != self.env.user.company_id.partner_id.id:
            self.product_packaging = False
            return {}
        if self.product_id.type == 'product':
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
            if float_compare(self.product_id.virtual_available, product_qty, precision_digits=precision) == -1:
                is_available = self._check_routing()
                if not is_available:
                    warning_mess = {
                        'title': _('Not enough inventory!'),
                        'message' : _('You plan to sell %s %s but you only have %s %s available!\nThe stock on hand is %s %s.') % \
                            (self.product_uom_qty, self.product_uom.name, self.product_id.virtual_available, self.product_id.uom_id.name, self.product_id.qty_available, self.product_id.uom_id.name)
                    }
                    return {'warning': warning_mess}
        return {}
    