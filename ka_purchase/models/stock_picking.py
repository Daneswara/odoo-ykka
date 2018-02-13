# -*- coding: utf-8 -*-

from collections import defaultdict
from odoo.addons import decimal_precision as dp
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

        
class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    date_transfer = fields.Datetime(string="Date of Transfer", copy=False)
    date_due_testing = fields.Date('Batas Pemeriksaan')
    is_return_picking = fields.Boolean('Is Return Picking', compute='get_is_return_picking')
    pengadaan = fields.Selection([('RD','SP Direksi'),('RP','SP Pabrik')], store=True, compute='get_pengadaan_sp')
    
    
    @api.multi
    @api.depends('move_lines','move_lines.origin')
    def get_pengadaan_sp(self):
        for this in self:
            res = False
            for move in this.move_lines:
                if move.origin:
                    po_src = self.env['purchase.order'].search([('name','=',move.origin),('state','!=','draft')], limit=1)
                    if po_src:
                        if po_src.order_type == 'lokal':
                            res = 'RP'
                        else:
                            res = 'RD'
                        break
            this.pengadaan = res
                        
    
    @api.multi
    @api.depends('move_lines.origin_returned_move_id')
    def get_is_return_picking(self):
        for this in self:
            res = False
            for move in this.move_lines:
                if move.origin_returned_move_id:
                    res = True
                    break
            this.is_return_picking = res
    
    @api.onchange('date_transfer')
    def onchange_date_transfer(self):
        if self.date_transfer:
            date_transfer = datetime.strptime(self.date_transfer, '%Y-%m-%d %H:%M:%S')
            self.date_due_testing = datetime.strftime(date_transfer + timedelta(days=10), '%Y-%m-%d')
    
    @api.multi
    def do_transfer(self): 
        super(StockPicking, self).do_transfer()
        for pick in self:
            move_products = []
            #set date in stock moves
            for move in pick.move_lines:
                move.write({'date': pick.date_transfer})
                is_exist = False
                for move_prod in move_products:
                    if move_prod.get('product_id') == move.product_id.id:
                        move_prod['quantity'] += move.product_uom_qty
                        is_exist = True
                if is_exist == False:
                    move_products.append({'product_id': move.product_id.id, 'quantity': move.product_uom_qty})
                    
            # set schedule date of destination move
            if pick.date_due_testing:
                test_date = datetime.strptime(pick.date_due_testing,'%Y-%m-%d')
                test_date = test_date.replace(hour=0, minute=0, second=0)
                test_date = datetime.strftime(test_date,'%Y-%m-%d %H:%M:%S')
                for mv in pick.move_lines:
                    if mv.move_dest_id:
                        mv.move_dest_id.write({'date_expected': test_date})
                        mv.move_dest_id.picking_id.write({'min_date': test_date})
            # process
            source_uid = self.env.user.company_id.intercompany_user_id.id
            
            reception_steps = pick.picking_type_id.warehouse_id.reception_steps
            backorder_location_usage = False
#             backorder_date_transfer = False
            for stmove in pick.move_lines:
                if not backorder_location_usage:
                    if stmove.move_orig_ids:
                        for move_orig in stmove.move_orig_ids:
                            backorder_location_usage = move_orig.location_id.usage
                            break
                    else:
                        po_src = self.env['purchase.order'].search([('name','=',stmove.origin)])
                        if po_src:
                            backorder_location_usage = 'supplier'
                else:
                    break
                
            if (reception_steps == 'two_steps' and backorder_location_usage == "supplier" and pick.location_id.usage == "transit") or \
               (reception_steps == 'one_step' and pick.location_id.usage == 'supplier'):
                # check WH use 1 or 2 steps receiving
                purchase_id = False
                for move in pick.move_lines:
                    if reception_steps == 'one_step':
                        if purchase_id == False and move.purchase_line_id:
                            purchase_id = move.purchase_line_id.order_id.id
                            break
                    elif reception_steps == 'two_steps': 
                        if move.move_orig_ids:
                            for move_orig in move.move_orig_ids:
                                if purchase_id == False and move_orig.purchase_line_id:
                                    purchase_id = move_orig.purchase_line_id.order_id.id
                                    break    
                        else:
                            po_src = self.env['purchase.order'].search([('name','=',stmove.origin)])
                            if po_src:
                                purchase_id = po_src.id
                
                for po in self.env['purchase.order'].browse(purchase_id):
                    len_inv = 0
                    if po.order_type == 'lokal':
                        
                        ka_number = po.name
                        if po.purchase_category_id.kode_ntb:
                            ka_number += '/' + po.purchase_category_id.kode_ntb
                            len_inv = len(po.invoice_ids) 
                            if len_inv >= 1 :
                                if len_inv < 9 :
                                    ka_number += '0' + str(len_inv + 1)
                                elif len_inv >= 9:
                                    ka_number += str(len_inv + 1)
                        
                    elif po.order_type == 'rkin':
                        po_source = self.env['purchase.order'].sudo(source_uid).browse(po.source_order_id.id)
                        po_company = po_source.company_id.internal_user_id.id
                        po_category = self.env['ka_account.payable.category'].sudo(po_company).search([('id','=', po_source.purchase_category_id.id)])
                        
                        ka_number = po.name
                        if po_category.kode_ntb:
                            ka_number += '/' + po_category.kode_ntb
                            len_inv = len(po.invoice_ids) 
                            if len_inv >= 1 :
                                if len_inv < 9 :
                                    ka_number += '0' + str(len_inv + 1)
                                elif len_inv >= 9:
                                    ka_number += str(len_inv + 1)
                        
#when user receive products from supplier, system will create vendor bill (NTB) automatically. set ka_number in vendor bill with format : PO number/kode NTB                         
                    invoice_id = self.env['account.invoice'].with_context(type='in_invoice').create({
                                        'purchase_id': po.id,
                                        'source_partner_id' : po.source_partner_id.id,
                                        'partner_id' : po.partner_id.id,
                                        'intercompany_invoice_type' : po.order_type,
                                        'purchase_category_id' : po.purchase_category_id.id,
                                        'operating_unit_id' : po.operating_unit_id.id,
                                        'origin' : po.name,
                                        'account_id' : po.partner_id.property_account_payable_id.id,
                                        'ka_number' : ka_number,
                                        'picking_date_transfer' : self.date_transfer,
                                        'purchase_date_order' : po.date_order,
                                        'purchase_date_planned' : po.date_planned
                                    })
                    for line in po.order_line:
                        if line in invoice_id.invoice_line_ids.mapped('purchase_line_id'):
                            continue
                        for prod in move_products:
                            if prod.get('product_id') == line.product_id.id:
                                data = invoice_id._prepare_invoice_line_from_po_line(line)
                                if data.get('quantity') > 0:
                                    data['invoice_id'] = invoice_id.id
                                    data['quantity'] = prod.get('quantity')
                                    self.env['account.invoice.line'].create(data)
                                    # compute denda
                                    scheduled_date = datetime.strptime(line.date_planned, '%Y-%m-%d %H:%M:%S')
                                    for move in pick.move_lines:
                                        if prod.get('product_id') == move.product_id.id:
                                            for quant in move.quant_ids:
                                                incoming_date = False
                                                for history in quant.history_ids:
                                                    if history.location_id.usage == 'supplier' and history.location_dest_id.id == pick.location_id.id:
                                                        incoming_date = datetime.strptime(history.date, '%Y-%m-%d %H:%M:%S')
                                                        break
                                                if incoming_date:
                                                    duration = incoming_date.date() - scheduled_date.date()
                                                    if duration.days > 0:
                                                        penalty_obj = self.env['account.penalty.config'].search([('min_days','<=',duration.days), ('max_days','>=',duration.days)], limit=1)
                                                        if not penalty_obj:
                                                            raise UserError('There is no configuration for ' + str(duration.days) + ' days overdue/penalty. Please contact your system administrator to configure it.')
                                                        amount = quant.qty * line.price_unit * penalty_obj.percent_penalty * 0.01
                                                        data_penalty = {'invoice_id' : invoice_id.id,
                                                                'product_id': move.product_id.id,
                                                                'due_date': datetime.strftime(scheduled_date, '%Y-%m-%d'),
                                                                'penalty_date': datetime.strftime(incoming_date, '%Y-%m-%d'),
                                                                'amount': amount}
                                                        self.env['account.penalty'].create(data_penalty)
                                break
                    invoice_id.write({'purchase_id': False})
#                     invoice_id.action_invoice_o/pen()
    
    
class stock_quant(models.Model):
    _inherit = "stock.quant"
    
    def _create_account_move_line(self, move, credit_account_id, debit_account_id, journal_id):
        # group quants by cost
        quant_cost_qty = defaultdict(lambda: 0.0)
        for quant in self:
            quant_cost_qty[quant.cost] += quant.qty

        AccountMove = self.env['account.move']
        for cost, qty in quant_cost_qty.iteritems():
            # additional : check if move QC (input -> stock)
            # set valuation_amount = unit price of stock move (purchase price)
            backorder_location_usage = False
            for move_orig in move.move_orig_ids:
                backorder_location_usage = move_orig.location_id.usage
            reception_steps = move.picking_id.picking_type_id.warehouse_id.reception_steps
            location_id_usage = move.location_id.usage
            
            move_lines = move._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
            if (reception_steps == 'two_steps' and backorder_location_usage == "supplier" and location_id_usage == "transit") or \
               (reception_steps == 'one_step' and location_id_usage == 'supplier'):                
                # move_lines = move.with_context(force_valuation_amount=move.price_unit)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
                move_lines = False
            #################################################
            if move_lines:
                date = self._context.get('force_period_date', fields.Date.context_today(self))
                new_account_move = AccountMove.create({
                    'journal_id': journal_id,
                    'line_ids': move_lines,
                    'date': date,
                    'ref': move.picking_id.name})
                new_account_move.post()    


class stock_move(models.Model):
    _inherit = "stock.move"
    
#     is_checked_for_penalty = fields.Boolean('Is Checked for Penalty')
    
    @api.multi
    def product_price_update_before_done(self):
        tmpl_dict = defaultdict(lambda: 0.0)
        
        this_reservation_steps = False
        backorder_location_usage = False
        for this in self:
            this_reservation_steps = this.picking_id.picking_type_id.warehouse_id.reception_steps
            for move_orig in this.move_orig_ids:
                backorder_location_usage = move_orig.location_id.usage
        
        if this_reservation_steps == 'two_steps' and backorder_location_usage == 'supplier':
            # adapt standard price on incomming moves if the product cost_method is 'average'
            for move in self.filtered(lambda move: (move.location_id.usage == 'transit' and move.product_id.cost_method == 'average')):
                transit_qty = 0.0
                for quant in self.env['stock.quant'].search([('product_id','=',move.product_id.id),('location_id.usage','=','transit')]):
                    transit_qty += quant.qty
                     
                product_tot_qty_available = move.product_id.qty_available + tmpl_dict[move.product_id.id] - transit_qty
                # if the incoming move is for a purchase order with foreign currency, need to call this to get the same value that the quant will use.
                if product_tot_qty_available <= 0:
                    new_std_price = move.get_price_unit()
                else:
                    # Get the standard price
                    amount_unit = move.product_id.standard_price
                    new_std_price = ((amount_unit * product_tot_qty_available) + (move.get_price_unit() * move.product_qty)) / (product_tot_qty_available + move.product_qty)
                     
                tmpl_dict[move.product_id.id] += move.product_qty
                # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
                move.product_id.with_context(force_company=move.company_id.id).write({'standard_price': new_std_price})
        
        elif this_reservation_steps == 'one_step' and this.location_id.usage == 'supplier':
            # adapt standard price on incomming moves if the product cost_method is 'average'
            for move in self.filtered(lambda move: (move.location_id.usage == 'supplier' and move.product_id.cost_method == 'average')):
                
                product_tot_qty_available = move.product_id.qty_available + tmpl_dict[move.product_id.id]
                # if the incoming move is for a purchase order with foreign currency, need to call this to get the same value that the quant will use.
                if product_tot_qty_available <= 0:
                    new_std_price = move.get_price_unit()
                else:
                    # Get the standard price
                    amount_unit = move.product_id.standard_price
                    new_std_price = ((amount_unit * product_tot_qty_available) + (move.get_price_unit() * move.product_qty)) / (product_tot_qty_available + move.product_qty)
                    
                tmpl_dict[move.product_id.id] += move.product_qty
                # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
                move.product_id.with_context(force_company=move.company_id.id).write({'standard_price': new_std_price})
        