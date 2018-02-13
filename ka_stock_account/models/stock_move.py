from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockMove(models.Model):
    _inherit = "stock.move"
    
    @api.model
    def default_get(self, fields):
        res = super(StockMove,self).default_get(fields)
        picking_type_ctx = self._context.get('default_picking_type_id')
        if picking_type_ctx:
            picking_type_id = self.env['stock.picking.type'].browse(picking_type_ctx)
            if picking_type_id.is_using_analytic_pkrat:
                last_sequence_pemakaian = self._context.get('last_sequence_pemakaian')
                if last_sequence_pemakaian != 0:
                    number_str = str(last_sequence_pemakaian + 1)
                    number_zero = 6 - len(number_str)
                    i = 1
                    while i <= number_zero:
                        number_str = '0' + number_str
                        i += 1
                    res['no_bukti_pengeluaran'] = 'P' + number_str
                    res['product_id'] = self._context.get('last_product_input', False)
                    res['account_id'] = self._context.get('last_account_input', False)
                    res['account_analytic_id'] = self._context.get('last_account_analytic_input', False)
        return res
        
    
    no_bukti_pengeluaran = fields.Char('No. Bukti')
    account_id = fields.Many2one('account.account', string='Account')
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    using_analytic_pkrat = fields.Boolean('Using Analytic PKRAT', related='picking_type_id.is_using_analytic_pkrat')
    quantity_io = fields.Float('Quantity I/O', compute='compute_quantity_io')
    
    
    @api.multi
    @api.depends('product_uom_qty')
    def compute_quantity_io(self):
        for this in self:
            warehouse_src = self.env['stock.warehouse'].search([('company_id','=',self.env.user.company_id.id)], limit=1)
            if warehouse_src:
                if this.location_id.id == warehouse_src.lot_stock_id.id or this.location_id.location_id.id == warehouse_src.lot_stock_id.id:
                    this.quantity_io = this.product_uom_qty * -1
                else:
                    this.quantity_io = this.product_uom_qty
    
    @api.onchange('account_analytic_id')
    def onchange_account_analytic_id(self):
        if self.account_analytic_id and not self.account_id:
            company_id = self.env.user.company_id.id
            partner_id = 'res.partner,' + str(self.env.user.company_id.partner_id.id)
            property_src = self.env['ir.property'].search([('name','=','account_pemakaian_barang'),
                                                           ('res_id','=',partner_id),
                                                           ('company_id','=',company_id)],limit=1)
            if property_src:
                value = property_src.value_reference
                value = value.split(',')
                self.account_id = int(value[1]) if len(value) == 2 else False
                
    @api.onchange('account_id')
    def onchange_account_id(self):
        if self.account_id:
            account_code = self.account_id.code
            if len(account_code) >= 6:
                analytic_code = account_code[:6]
                analytic_src = self.env['account.analytic.account'].search([('code','=',analytic_code)], limit=1)
                if analytic_src:
                    self.account_analytic_id = analytic_src.id
                
#     @api.onchange('product_uom_qty')
#     def onchange_product_uom_qty(self):
#         if self.product_id and self.using_analytic_pkrat and self.location_id.usage == 'internal':
#             quant_src = self.env['stock.quant'].search([('product_id','=',self.product_id.id),
#                                                         ('location_id','=',self.location_id.id),
#                                                         ('reservation_id','=',False)])
#             product_free_qty = sum(quant.qty for quant in quant_src)
#             if product_free_qty < self.product_uom_qty:
#                 raise UserError('Kuantum produk ini tidak mencukupi. Sisa kuantum sekarang adalah ' + str(product_free_qty) + ' ' + self.product_uom.name)
    
    @api.multi
    def _get_accounting_data_for_valuation(self):
        """ Return the accounts and journal to use to post Journal Entries for
        the real-time valuation of the quant. """
        self.ensure_one()
        accounts_data = self.product_id.product_tmpl_id.get_product_accounts()

        if self.location_id.valuation_out_account_id:
            acc_src = self.location_id.valuation_out_account_id.id
        else:
            acc_src = accounts_data['stock_input'].id
            # additional by PAA, to check stock output category
            if self.picking_id.using_analytic_pkrat:
                acc_src = self.account_id.id

        if self.location_dest_id.valuation_in_account_id:
            acc_dest = self.location_dest_id.valuation_in_account_id.id
        else:
            acc_dest = accounts_data['stock_output'].id
            # additional by PAA, to check stock output category
            if self.picking_id.using_analytic_pkrat:
                acc_dest = self.account_id.id

        acc_valuation = accounts_data.get('stock_valuation', False)
        if acc_valuation:
            acc_valuation = acc_valuation.id
        if not accounts_data.get('stock_journal', False):
            raise UserError(_('You don\'t have any stock journal defined on your product category, check if you have installed a chart of accounts'))
        if not acc_src:
            raise UserError(_('Cannot find a stock input account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (self.product_id.name))
        if not acc_dest:
            raise UserError(_('Cannot find a stock output account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (self.product_id.name))
        if not acc_valuation:
            raise UserError(_('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))
        journal_id = accounts_data['stock_journal'].id
        return journal_id, acc_src, acc_dest, acc_valuation
    
    
    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        self.ensure_one()
        if self._context.get('force_valuation_amount'):
            valuation_amount = self._context.get('force_valuation_amount')
        else:
            if self.product_id.cost_method == 'average':
                valuation_amount = cost if self.location_id.usage == 'supplier' and self.location_dest_id.usage == 'internal' else self.product_id.standard_price
            else:
                valuation_amount = cost if self.product_id.cost_method == 'real' else self.product_id.standard_price
        # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
        # the company currency... so we need to use round() before creating the accounting entries.
        debit_value = self.company_id.currency_id.round(valuation_amount * qty)

        # check that all data is correct
        if self.company_id.currency_id.is_zero(debit_value):
            if self.product_id.cost_method == 'standard':
                raise UserError(_("The found valuation amount for product %s is zero. Which means there is probably a configuration error. Check the costing method and the standard price") % (self.product_id.name,))
            return []
        credit_value = debit_value

        if self.product_id.cost_method == 'average' and self.company_id.anglo_saxon_accounting:
            # in case of a supplier return in anglo saxon mode, for products in average costing method, the stock_input
            # account books the real purchase price, while the stock account books the average price. The difference is
            # booked in the dedicated price difference account.
            if self.location_dest_id.usage == 'supplier' and self.origin_returned_move_id and self.origin_returned_move_id.purchase_line_id:
                debit_value = self.origin_returned_move_id.price_unit * qty
            # in case of a customer return in anglo saxon mode, for products in average costing method, the stock valuation
            # is made using the original average price to negate the delivery effect.
            if self.location_id.usage == 'customer' and self.origin_returned_move_id:
                debit_value = self.origin_returned_move_id.price_unit * qty
                credit_value = debit_value
                
        partner_id = (self.picking_id.partner_id and self.env['res.partner']._find_accounting_partner(self.picking_id.partner_id).id) or False
        debit_line_vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': self.picking_id.name,
            'partner_id': partner_id,
            'debit': debit_value,
            'credit': 0,
            'account_id': debit_account_id,
            'analytic_account_id': self.account_analytic_id.id if debit_account_id in (
                                   self.location_id.valuation_in_account_id.id,
                                   self.location_id.valuation_out_account_id.id,
                                   self.location_dest_id.valuation_in_account_id.id,
                                   self.location_dest_id.valuation_out_account_id.id) else None
        }
        
        credit_line_vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': self.picking_id.name,
            'partner_id': partner_id,
            'credit': credit_value,
            'debit': 0,
            'account_id': credit_account_id,
            'analytic_account_id': self.account_analytic_id.id if credit_account_id in (
                                   self.location_id.valuation_in_account_id.id,
                                   self.location_id.valuation_out_account_id.id,
                                   self.location_dest_id.valuation_in_account_id.id,
                                   self.location_dest_id.valuation_out_account_id.id) else None
        }

        # additional by PAA, to check stock output category
        if self.picking_id.using_analytic_pkrat:
            picking_type_return_src = self.env['stock.picking.type'].search([('return_picking_type_id','=',self.picking_type_id.id)])
            if self.origin_returned_move_id or picking_type_return_src:
                credit_line_vals['analytic_account_id'] = self.account_analytic_id.id
            else:
                debit_line_vals['analytic_account_id'] = self.account_analytic_id.id
        
        res = [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
        if credit_value != debit_value:
            # for supplier returns of product in average costing method, in anglo saxon mode
            diff_amount = debit_value - credit_value
            price_diff_account = self.product_id.property_account_creditor_price_difference
            if not price_diff_account:
                price_diff_account = self.product_id.categ_id.property_account_creditor_price_difference_categ
            if not price_diff_account:
                raise UserError(_('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))
            price_diff_line = {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': self.picking_id.name,
                'partner_id': partner_id,
                'credit': diff_amount > 0 and diff_amount or 0,
                'debit': diff_amount < 0 and -diff_amount or 0,
                'account_id': price_diff_account.id,
            }
            res.append((0, 0, price_diff_line))
        return res