# -*- coding: utf-8 -*-
from odoo.addons import decimal_precision as dp
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
import math
        
        
class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    @api.model
    def default_get(self, fields):
        res = super(StockPicking, self).default_get(fields)
        active_model = self._context.get('active_model',False)
        if active_model == 'stock.picking.type':
            active_id = self._context.get('active_id',False)
            for type in self.env['stock.picking.type'].browse(active_id):
                if type.is_do_kontrak_a == True:
                    move_line = {'product_id' : self.env.user.company_id.product_sugar_id.id,
                                 'product_uom' : self.env.user.company_id.product_sugar_id.uom_id.id,
                                 'product_uom_qty' : 1,
                                 'scrapped' : False,
                                 'state' : 'draft',
                                 'name' : self.env.user.company_id.product_sugar_id.display_name,
                                 'date_expected' : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                 'location_id' : type.default_location_src_id.id,
                                 'location_dest_id' : type.default_location_dest_id.id,
                                  }
                    res['partner_id'] = type.default_partner_id.id
                    res['move_lines'] = [(0,0,move_line)]
        return res
    
    USAGE_LOCATION = [
        ('supplier', 'Vendor Location'),
        ('view', 'View'),
        ('internal', 'Internal Location'),
        ('customer', 'Customer Location'),
        ('inventory', 'Inventory Loss'),
        ('procurement', 'Procurement'),
        ('production', 'Production'),
        ('transit', 'Transit Location')]
    picking_type = [
        ('incoming', 'Vendors'),
        ('outgoing', 'Customers'),
        ('internal', 'Internal')]
    location_dest_usage = fields.Selection(USAGE_LOCATION, string='Destination Type', related='location_dest_id.usage')
    location_usage = fields.Selection(USAGE_LOCATION, string='Source Type', related='location_id.usage')
    picking_code_type = fields.Selection(picking_type, string='Picking Type', related='picking_type_id.code')
    using_analytic_pkrat = fields.Boolean('Using Analytic PKRAT', related='picking_type_id.is_using_analytic_pkrat')
    total_product_code_manual = fields.Float('Total Kode Produk (Manual)')
    total_product_qty_manual = fields.Float('Total Kuantum (Manual)')
    total_product_code = fields.Float('Total Kode Produk', compute='compute_product_moves')
    total_product_qty = fields.Float('Total Kuantum', compute='compute_product_moves')
    date_printed = fields.Datetime('Printed Date', track_visibility='onchange')
    
    last_sequence_pemakaian = fields.Integer('Last Sequence Pemakaian Barang', compute='get_last_sequence_pemakaian')
    last_product_input = fields.Many2one('product.product', 'Last Product Input', compute='get_last_product_input')
    last_account_input = fields.Many2one('account.account', 'Last Account Input', compute='get_last_product_input')
    last_account_analytic_input = fields.Many2one('account.analytic.account', 'Last Analytic Account Input', compute='get_last_product_input')
    
    @api.multi
    @api.depends('move_lines')
    def get_last_sequence_pemakaian(self):
        for this in self:
            list_codes = [move.no_bukti_pengeluaran for move in this.move_lines]
            if list_codes != []:
                list_codes.sort(reverse=True)
                if list_codes[0] != False:
                    this.last_sequence_pemakaian = int(list_codes[0][1:])
    
    @api.multi
    @api.depends('move_lines')
    def get_last_product_input(self):
        for this in self:
            last_product = False
            last_account = False
            last_account_analytic = False
            for move in this.move_lines:
                last_product = move.product_id.id
                last_account = move.account_id.id
                last_account_analytic = move.account_analytic_id.id
            this.last_product_input = last_product
            this.last_account_input = last_account
            this.last_account_analytic_input = last_account_analytic
    
    @api.multi
    @api.depends('move_lines')
    def compute_product_moves(self):
        for this in self:
            res_code = 0.0
            res_qty = 0.0
            for move in this.move_lines:
                if move.product_id and move.product_id.default_code:
                    product_code = move.product_id.default_code
                    res_code += float(product_code.replace('.',''))
                res_qty += move.product_uom_qty
            this.total_product_code = res_code
            this.total_product_qty = res_qty

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):

    #     res = super(StockPicking, self).fields_view_get(view_id=view_id, view_type=view_type,toolbar=toolbar, submenu=submenu)


    #     if view_type == 'form':

    #         if self.picking_code_type != 'internal':
    #             doc = etree.XML(res['arch']) 
    #             nodes = doc.xpath("//fields[@name='pack_operation_product_ids']/tree/fields[@name='reject']")
    #             print nodes
    #             for node in nodes:
    #                 node.set('invisible', '1')
    #                 setup_modifiers(node, res['fields']['reject'])
    #             res['arch'] = etree.tostring(doc)
    #     return res
    
    @api.multi
    def action_confirm(self):
        super(StockPicking,self).action_confirm()
        # check total product qty & product code, raise warning if not same
        print self._context.get('not_check_product_info')
        if not self._context.get('not_check_product_info'):
            is_return = False
            for move in self.move_lines:
                if move.origin_returned_move_id:
                    is_return = True
                    break
            if is_return:
                self.write({'total_product_code_manual': self.total_product_code, 'total_product_qty_manual': self.total_product_qty})
                    
            if self.using_analytic_pkrat:
                if self.total_product_code_manual != self.total_product_code:
                    raise UserError('Total kode produk tidak sama dengan total kode produk yang diinput manual!')
                if self.total_product_qty_manual != self.total_product_qty:
                    raise UserError('Total kuantum produk tidak sama dengan total kuantum produk yang diinput manual!')
    
    @api.multi
    def action_assign(self):
        """ Check availability of picking moves.
        This has the effect of changing the state and reserve quants on available moves, and may
        also impact the state of the picking as it is computed based on move's states.
        @return: True
        """        
        self.filtered(lambda picking: picking.state == 'draft').action_confirm()
        moves = self.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))
        if not moves:
            raise UserError(_('Nothing to check the availability for.'))
        
        # check availability for kontrak A
        if self.picking_type_id.is_do_kontrak_a:
            moves.sudo(self.company_id.intercompany_user_id.id).action_assign()
        else:
            moves.action_assign()
        return True
    
    
    @api.multi
    def do_transfer(self):
        super(StockPicking, self).do_transfer()
#         From stock.picking, when Validate the form, then create Journal Entries 
        for this in self:
            # GULA KONTRAK A
            return_move = False
            for move in this.move_lines:
                if move.origin_returned_move_id:
                    return_move = True
                    break
            if return_move == False and this.picking_type_id.is_do_kontrak_a:
                acc_move_obj = this.env['account.move']
                j_items = []

                journal_id = this.env['account.journal'].search([('name','=','Stock Journal'), ('company_id','=', this.env.user.company_id.id)])
                data_entry = {
                    'journal_id':journal_id.id,
                    'ref': this.name,
                    'company_id': this.env.user.company_id.id,
                    'line_ids': j_items                
                }
                acc_move_create1 = acc_move_obj.create(data_entry)
                
                acc_move_create2 = False
                if this.location_dest_id.company_id:
                    acc_move_create2 = acc_move_obj.create(data_entry)
# ---------------------------------------------------------------------------------------------------------
                source_uid = this.env.user.company_id.intercompany_user_id.id
                company_obj = self.env['res.company'].sudo(source_uid).search([('partner_id','=', this.partner_id.id)])
                journal_id = this.env['account.journal'].sudo(company_obj.internal_user_id.id).search([('name','=','Stock Journal'), ('company_id','=', company_obj.id)])
                
                data_entry = {
                    'journal_id':journal_id.id,
                    'ref': this.name,
                    'line_ids': j_items
                }
                acc_move_create3 = acc_move_obj.sudo(company_obj.internal_user_id.id).with_context(company_id=company_obj.id).create(data_entry)
# ---------------------------------------------------------------------------------------------------------
                default_customer_tax_id = self.env['ir.values'].get_default('product.template', 'taxes_id', company_id = self.env.user.company_id.id) or False
                if not default_customer_tax_id:
                    raise UserError('Please define default customer tax first for this company.')
                tax_id = self.env['account.tax'].browse(default_customer_tax_id)
                
                def_customer_tax_direksi = self.env['ir.values'].sudo(company_obj.internal_user_id.id).get_default('product.template', 'taxes_id', company_id = company_obj.id) or False
                if not def_customer_tax_direksi:
                    raise UserError('Please define default customer tax first for this company.')
                tax_direksi = self.env['account.tax'].sudo(company_obj.internal_user_id.id).with_context(company_id=company_obj.id).browse(def_customer_tax_direksi)
                
                for stock_pack in this.pack_operation_product_ids:
#                     stock_pack = this.env['stock.pack.operation'].search([('picking_id','=',this.id)], limit=1)
                    product_name = stock_pack.product_id.display_name
                    
                    stock_move = this.env['stock.move'].search([('picking_id','=',this.id)])
                    acc_config = this.env['res.company'].browse(this.env.user.company_id.id)
                    p1 = stock_move.product_uom_qty * acc_config.default_price_contract_a
                    tax = tax_id.amount / 100
                    p2 = p1*tax
                    debit = p1+p2
                    p3 = stock_pack.product_id.standard_price*stock_move.product_uom_qty # Cost price * quantity

# ------------------------------------------ JOURNAL ITEMS #1 :: PG ---------------------------------------------------                    
                    vals1 = {
                        'account_id':this.partner_id.property_account_receivable_id.id,
                        'name': product_name,
                        'partner_id': this.partner_id.id,
                        'move_id': acc_move_create1.id,
                        'debit': debit,
                        'credit': 0
                    }
                    j_items.append((0, 0, vals1))

                    vals2 = {
                        'account_id':stock_pack.product_id.property_account_income_id.id or stock_pack.product_id.categ_id.property_account_income_categ_id.id,
                        'name': product_name,
                        'partner_id': this.partner_id.id,
                        'move_id': acc_move_create1.id,
                        'debit': 0,
                        'credit': p1
                    }
                    j_items.append((0, 0, vals2))
                    
                    vals3 = {
                        'account_id': tax_id.account_id.id,
                        'name': product_name,
                        'partner_id': this.partner_id.id,
                        'move_id': acc_move_create1.id,
                        'debit': 0,
                        'credit': p2
                    }
                    j_items.append((0, 0, vals3))

                    acc_move_create1.line_ids = j_items

# ------------------------------------------ JOURNAL ITEMS #2 :: PG --------------------------------------------------------
                    if acc_move_create2:
                        j_items = []
                        vals1 = {
                            'account_id':stock_pack.product_id.property_account_expense_id.id or stock_pack.product_id.categ_id.property_account_expense_categ_id.id,
                            'name': product_name,
                            'partner_id': this.partner_id.id,
                            'move_id': acc_move_create2.id,
                            'debit': p3,
                            'credit': 0
                        }
                        j_items.append((0, 0, vals1))
     
                        vals2 = {
                            'account_id': stock_pack.product_id.categ_id.property_stock_valuation_account_id.id,
                            'name': product_name,
                            'partner_id': this.partner_id.id,
                            'move_id': acc_move_create2.id,
                            'debit': 0,
                            'credit': p3
                        }
                        j_items.append((0, 0, vals2))
     
                        acc_move_create2.line_ids = j_items

# ------------------------------------------ JOURNAL ITEMS #3 :: DIREKSI --------------------------------------------------                    
                    j_items = []
                    tax_dir = tax_direksi.amount/100
                    p1 = stock_move.product_uom_qty * this.company_id.default_price_contract_a
                    p2 = p1*tax_dir
                    
                    vals1 = {
                        'account_id': this.company_id.partner_id.sudo(company_obj.internal_user_id.id).property_account_payable_id.id,
                        'name': product_name,
                        'partner_id': this.company_id.partner_id.id,
                        'move_id': acc_move_create3.id,
                        'debit': p2,
                        'credit': 0
                    }
                    j_items.append((0, 0, vals1))
                    vals2 = {
                        'account_id': tax_direksi.sudo(company_obj.internal_user_id.id).with_context(company_id=company_obj.id).account_id.id,
                        'name': product_name,
                        'partner_id': this.company_id.partner_id.id,
                        'move_id': acc_move_create3.id,
                        'debit': 0,
                        'credit': p2
                    }
                    j_items.append((0, 0, vals2))
                    
                    acc_move_create3.line_ids = j_items
                
                acc_move_create1.post()
                if acc_move_create2:
                    acc_move_create2.post()
                acc_move_create3.sudo(company_obj.internal_user_id.id).with_context(company_id=company_obj.id).post()
                
                # change company of quants become direksi
                if not self.location_dest_id.company_id:
                    for move in this.move_lines:
                        for quant in move.quant_ids:
                            self._cr.execute('update stock_quant set company_id=%s where id=%s', (company_obj.id, quant.id))
    
    @api.multi
    def print_report_stock_product(self):
        report_obj = self.env['report']
        template = 'ka_stock_account.report_stock_product_receive'
        report = report_obj._get_report_from_name(template)
        domain = {}
        values = {
            'ids': self.ids,
            'model': report.model,
            'form': domain
        }
        return report_obj.get_action(self, template, data=values)
    
    ########### REPORT RETURN SUPPLIER ##############
    def get_purchase_id(self):
        res = False
        for move in self.move_lines:
            if move.origin_returned_move_id.purchase_line_id:
                res = move.origin_returned_move_id.purchase_line_id.order_id
                break
        return res
    
    def get_rows_return_supplier(self):
        count = 1
        rows = list()
        cols = list()
        for move in self.move_lines:
            row_note = math.ceil(len(move.note)/100.0)
            vals = {'code': move.product_id.default_code,
                    'name': move.product_id.name,
                    'description' : move.product_id.description,
                    'qty': move.product_uom_qty,
                    'uom': move.product_uom.name,
                    'note': move.note,
                    'row_note': row_note}
            if count == 6:
                cols.append(vals)
                rows.append(cols)
                cols = list()
                count = 1
            else:
                cols.append(vals)
                count += 1
        if count > 0:
            for i in range(7-count):
                vals = {'code': '-',
                        'name': '-',
                        'description' :'-',
                        'qty': '-',
                        'uom': '-',
                        'note': '-',
                        'row_note': 1}
                cols.append(vals)
            rows.append(cols)
        return rows


class StockPickingType(models.Model):
    _inherit="stock.picking.type"
    
    is_do_kontrak_a = fields.Boolean('DO Kontrak A')
    default_partner_id = fields.Many2one('res.partner', string='Partner')
    is_using_analytic_pkrat = fields.Boolean('Using Analytic PKRAT')
    

class StockPackOperation(models.Model):
    _inherit="stock.pack.operation"

    reject =  fields.Float('Reject',default=0.0, digits=dp.get_precision('Product Unit of Measure'))
    alasan = fields.Text('Alasan')
    picking_code = fields.Selection(related="picking_id.picking_code_type")

    @api.multi
    def save_reject(self):
        # TDE FIXME: does not seem to be used -> actually, it does
        # TDE FIXME: move me somewhere else, because the return indicated a wizard, in pack op, it is quite strange
        # HINT: 4. How to manage lots of identical products?
        # Create a picking and click on the Mark as TODO button to display the Lot Split icon. A window will pop-up. Click on Add an item and fill in the serial numbers and click on save button
        
        self.qty_done = self.product_qty - self.reject
        for pack in self:
            if pack.product_id.tracking != 'none':
                pack.write({'reject': sum(pack.pack_lot_ids.mapped('qty'))})

        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def show_rejects(self):
        # TDE FIXME: does not seem to be used
        view_id = self.env.ref('ka_stock_account.view_pack_reject_form_save').id
        return {
            'name': _('Operation Reject'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.pack.operation',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context}
            
