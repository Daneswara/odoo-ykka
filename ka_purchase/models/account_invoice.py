from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError
from datetime import datetime
import math
import pytz

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    _template_ntb_report = 'ka_purchase.template_report_ntb'
    
    purchase_date_order = fields.Datetime(string="Tanggal SP", copy=False)
    purchase_date_planned = fields.Datetime(string="Tanggal Batas", copy=False)
    picking_date_transfer = fields.Datetime(string="Tanggal Delivered", copy=False)
    
    @api.model
    def default_get(self, fields):
        res = super(AccountInvoice, self).default_get(fields)
        active_model = self._context.get('active_model',False)
        inv_type = self._context.get('type',False)
        if active_model == 'purchase.order' and inv_type == 'in_invoice':
            active_id = self._context.get('active_id',False)
            for purchase in self.env['purchase.order'].browse(active_id):
                res['intercompany_invoice_type'] = purchase.order_type
                res['source_partner_id'] = purchase.source_partner_id.id
                res['operating_unit_id'] = purchase.operating_unit_id.id    
                res['purchase_category_id'] = purchase.purchase_category_id.id
        return res
        
    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self): 
        super(AccountInvoice,self)._onchange_partner_id()
        if self.intercompany_invoice_type == 'lokal':
            self.account_id = self.purchase_category_id.property_account_payable_id.id

    def _prepare_invoice_line_from_po_line(self, line):
        if line.product_id.purchase_method == 'purchase':
            qty = line.product_qty - line.qty_invoiced
        else:
            qty = line.qty_received - line.qty_invoiced
        if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
            qty = 0.0
        taxes = line.taxes_id
        invoice_line_tax_ids = self.purchase_id.fiscal_position_id.map_tax(taxes)
        invoice_line = self.env['account.invoice.line']
        data = {
            'purchase_line_id': line.id,
            'name': self.purchase_id.name+': '+line.name,
            'origin': self.purchase_id.origin,
            'uom_id': line.product_uom.id,
            'product_id': line.product_id.id,
            'account_id': invoice_line.with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
            'price_unit': line.order_id.currency_id.compute(line.price_unit, self.currency_id, round=False),
            'quantity': qty,
            'discount': 0.0,
            'account_analytic_id': line.account_analytic_id.id,
            'analytic_tag_ids': line.analytic_tag_ids.ids,
            'invoice_line_tax_ids': invoice_line_tax_ids.ids
        }
        account = invoice_line.get_invoice_line_account('in_invoice', line.product_id, self.purchase_id.fiscal_position_id, self.env.user.company_id)
        if account:
            data['account_id'] = account.id

        user = self.env.user.company_id.intercompany_user_id.id
        source_order = line.order_id.sudo(user).source_order_id.id
        source_company = line.order_id.sudo(user).source_order_id.sudo(user).company_id
        if line.account_analytic_id:
            if source_order:
                if line.account_analytic_id.sudo(user).pkrat_type == '1':
                    data['account_id'] = source_company.partner_id.sudo(self.env.user.id).account_investasi_baru.id
                elif line.account_analytic_id.sudo(user).pkrat_type == '2':
                    data['account_id'] = source_company.partner_id.sudo(self.env.user.id).account_perbaikan_luar_biasa.id
                elif line.account_analytic_id.sudo(user).pkrat_type == '3':
                    data['account_id'] = source_company.partner_id.sudo(self.env.user.id).account_inventaris.id
            elif not source_order:
                if line.account_analytic_id.sudo(user).pkrat_type == '1':
                    data['account_id'] = line.order_id.operating_unit_id.account_investasi_baru.id
                elif line.account_analytic_id.sudo(user).pkrat_type == '2':
                    data['account_id'] = line.order_id.operating_unit_id.account_perbaikan_luar_biasa.id
                elif line.account_analytic_id.sudo(user).pkrat_type == '3':
                    data['account_id'] = line.order_id.operating_unit_id.account_inventaris.id     
        return data

    # Load all unsold PO lines
    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id

        if not self.purchase_date_order:
            self.purchase_date_order = self.purchase_id.date_order
        
        if not self.purchase_date_planned:
            self.purchase_date_planned = self.purchase_id.date_planned
            
        self.date_invoice = fields.Date.today()
            
        source_uid = self.env.user.company_id.intercompany_user_id.id
        len_inv = 0
        if self.purchase_id.order_type == 'lokal':
            self.ka_number = self.purchase_id.name
            if self.purchase_id.purchase_category_id.kode_ntb:
                self.ka_number += '/' + self.purchase_id.purchase_category_id.kode_ntb
                len_inv = len(self.purchase_id.invoice_ids) 
                if len_inv >= 1 :
                    if len_inv < 9 :
                        self.ka_number += '0' + str(len_inv + 1)
                    elif len_inv >= 9:
                        self.ka_number += str(len_inv + 1)
            
        elif self.purchase_id.order_type == 'rkin':
            po_src = self.env['purchase.order'].sudo(source_uid).search([('id','=', self.purchase_id.source_order_id.id)])
            po_company = po_src.company_id.internal_user_id.id
            po_category = self.env['ka_account.payable.category'].sudo(po_company).search([('id','=', po_src.purchase_category_id.id)]) 
            self.ka_number = self.purchase_id.name
            if po_category.kode_ntb:
                self.ka_number += '/' + po_category.kode_ntb
                len_inv = len(self.purchase_id.invoice_ids)
                if len_inv >=1 :
                    if len_inv < 9 :
                        self.ka_number += '0' + str(len_inv + 1)
                    elif len_inv >= 9 :
                        self.ka_number += str(len_inv + 1)
                    
        new_lines = self.env['account.invoice.line']
        for line in self.purchase_id.order_line:
            # print line.order_id.name, line.product_id.name, line.qty_received
            # print "===================="
            # Load a PO line only once
            if line in self.invoice_line_ids.mapped('purchase_line_id'):
                continue
            data = self._prepare_invoice_line_from_po_line(line)
            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line

        self.invoice_line_ids += new_lines
        
        amount_penalty = 0.0
        penalties = []
        for line in self.purchase_id.order_line:
            scheduled_date = datetime.strptime(line.date_planned, '%Y-%m-%d %H:%M:%S')
            
            if line.product_id.type == 'service':
                for inv_line in self.invoice_line_ids:
                    bill_date = fields.Date.from_string(self.date_invoice)
                    scheduled_date = fields.Date.from_string(line.date_planned)
                    duration = bill_date - scheduled_date
                    if duration.days > 0:
                        penalty_obj = self.env['account.penalty.config'].search([('min_days','<=',duration.days), ('max_days','>=',duration.days)], limit=1)
                        if not penalty_obj:
                            raise UserError('There is no configuration for ' + str(duration.days) + ' days overdue/penalty. Please contact your system administrator to configure it.')
                        amount = inv_line.quantity * line.price_unit * penalty_obj.percent_penalty * 0.01
                        data = {'product_id': inv_line.product_id.id,
                                'due_date': datetime.strftime(scheduled_date, '%Y-%m-%d'),
                                'penalty_date': datetime.strftime(bill_date, '%Y-%m-%d'),
                                'amount': amount}
                        amount_penalty += amount
                        penalties.append((0, 0, data))
            
            for move in self.env['stock.move'].search([('purchase_line_id','=',line.id), ('state','=','done')]):
                if move.picking_id.date_transfer:
                    moved_date = datetime.strptime(move.picking_id.date_transfer, '%Y-%m-%d %H:%M:%S')
                    duration = moved_date.date() - scheduled_date.date()
                    if duration.days > 0:
                        penalty_obj = self.env['account.penalty.config'].search([('min_days','<=',duration.days), ('max_days','>=',duration.days)], limit=1)
                        if not penalty_obj:
                            raise UserError('There is no configuration for ' + str(duration.days) + ' days overdue/penalty. Please contact your system administrator to configure it.')
                        amount = move.product_uom_qty * line.price_unit * penalty_obj.percent_penalty * 0.01
                        data = {'product_id': move.product_id.id,
                                'due_date': datetime.strftime(scheduled_date, '%Y-%m-%d'),
                                'penalty_date': datetime.strftime(moved_date, '%Y-%m-%d'),
                                'amount': amount}
                        amount_penalty += amount
                        penalties.append((0, 0, data))
                    
        self.amount_penalty = amount_penalty
        self.penalty_ids = False
        self.penalty_ids = penalties
        
        self.purchase_id = False
        return {}
    
    @api.multi
    def invoice_validate(self):
        for invoice in self:
            #refuse to validate a vendor bill/refund if there already exists one with the same reference for the same partner,
            #because it's probably a double encoding of the same bill/refund
            if invoice.type in ('in_invoice', 'in_refund') and invoice.reference:
                if self.search([('type', '=', invoice.type), ('reference', '=', invoice.reference), ('company_id', '=', invoice.company_id.id), ('commercial_partner_id', '=', invoice.commercial_partner_id.id), ('id', '!=', invoice.id)]):
                    raise UserError(_("Duplicated vendor reference detected. You probably encoded twice the same vendor bill/refund."))
            # ADD : if invoice from factory
            if invoice.intercompany_invoice_type == 'rkin':
                self._cr.execute("update account_invoice set state='paid' where id=%s",(invoice.id,))
                return True
            else:
                return self.write({'state': 'open'})
    
    @api.multi
    def action_invoice_open(self):
        for this in self:
            purchase_id = False
            for inv_line in this.invoice_line_ids:
                if purchase_id == False:
                    if inv_line.purchase_line_id:
                        purchase_id = inv_line.purchase_line_id.order_id.id
                else:
                    if inv_line.purchase_line_id and inv_line.purchase_line_id.order_id.id != purchase_id:
                        raise UserError('Sorry, you can not validate this invoice because it created from several PO.')
                        
            for order in self.env['purchase.order'].browse(purchase_id):
                if this.intercompany_invoice_type == 'rkin':
                    inv_user = self.env.user.company_id.intercompany_user_id.id
                    source_order = order.sudo(inv_user).source_order_id
                    company_ctx = source_order.sudo(inv_user).company_id.id
                    inv_user2 = False
                    for inv_company in self.env['res.company'].sudo().search([('partner_id','=',this.partner_id.id)], limit=1):
                        inv_user2 = inv_company.internal_user_id.id
                    inv_context = {'type': 'in_invoice', 
                                   'company_id': company_ctx,
                                   'default_purchase_id': source_order.id}
                    inv_model = self.env['account.invoice'].sudo(inv_user).with_context(inv_context)
                    inv_account_id = False
                    for inv_account in self.env['ka_account.payable.category'].sudo(inv_user2).with_context(inv_context).search([('code','=',this.purchase_category_id.code)]):
                        inv_account_id = inv_account.property_account_payable_id.id
                    inv_vals = {'ka_number': this.ka_number,
                                'partner_id': source_order.partner_id.id,
                                'origin': source_order.name,
                                'journal_id': inv_model._default_journal().id,
                                'user_id': inv_user,
                                'account_id': inv_account_id,
                                'company_id': company_ctx,
                                'purchase_category_id': this.purchase_category_id.id,
                                'intercompany_invoice_type': 'rkout',
                                'operating_unit_id': source_order.operating_unit_id.id,
                                'source_invoice_id': this.id,
                                'date_invoice': this.date_invoice,
                                'date_due': this.date_due,
                                'picking_date_transfer' : this.picking_date_transfer,
                                'purchase_date_order' : this.purchase_date_order,
                                'purchase_date_planned' : this.purchase_date_planned
                                }
                    inv_create = inv_model.create(inv_vals)
                    
                    this.dest_invoice_id = inv_create.id
                    inv_line_account_id = source_order.sudo(inv_user2).with_context(inv_context).operating_unit_id.property_account_receivable_id.id
#                     print ">>>>>>>>>>>>>>>>>>>>>>>> ", inv_account.property_account_payable_id.name
                    for line in this.invoice_line_ids:
                        data = {
                            'invoice_id': inv_create.id,
                            'purchase_line_id': line.purchase_line_id.source_order_line_id.id,
                            'name': line.name,
                            'origin': source_order.origin,
                            'uom_id': line.uom_id.id,
                            'product_id': line.product_id.id,
                            'account_id': inv_line_account_id,
                            'price_unit': source_order.currency_id.sudo(inv_user).compute(line.price_unit, inv_create.currency_id),
                            'quantity': line.quantity,
                            'progress_percent': line.progress_percent,
                            'account_analytic_id': line.account_analytic_id.id,
                            'invoice_line_tax_ids': line.invoice_line_tax_ids.ids
                        }
                        self.env['account.invoice.line'].sudo(inv_user).with_context(inv_context).create(data)
                    
#                     src_penalty_obj = self.env['account.penalty'].search([('invoice_id','=',inv_create.id)])
                    for penalty in this.penalty_ids:
                        data = {
                            'invoice_id': inv_create.id,
                            'product_id': penalty.product_id.id,
                            'amount': penalty.amount,
                            'due_date': penalty.due_date,
                            'penalty_date': penalty.penalty_date,
                            'currency_id': penalty.currency_id.id,
                        }
                        self.env['account.penalty'].sudo(inv_user).with_context(inv_context).create(data)
                        
                    inv_create.sudo(inv_user).with_context(company_id=company_ctx).action_invoice_open()
        return super(AccountInvoice,self).action_invoice_open()
    
    @api.multi
    def get_due_testing(self):
        for this in self:
            picking = False
            for line in self.invoice_line_ids:
                for move in self.env['stock.move'].search([('purchase_line_id','=',line.purchase_line_id.id)]):
                    picking = move.picking_id
                    break
            due_testing = datetime.strftime(datetime.strptime(picking.date_due_testing, '%Y-%m-%d'), '%d-%m-%Y')
        return due_testing
    
#     @api.multi
#     def action_move_create(self):
#         """ Creates invoice related analytics and financial move lines """
#         account_move = self.env['account.move']
# 
#         for inv in self:
#             if not inv.journal_id.sequence_id:
#                 raise UserError(_('Please define sequence on the journal related to this invoice.'))
#             if not inv.invoice_line_ids:
#                 raise UserError(_('Please create some invoice lines.'))
#             if inv.move_id:
#                 continue
# 
#             ctx = dict(self._context, lang=inv.partner_id.lang)
# 
#             if not inv.date_invoice:
#                 inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
#             date_invoice = inv.date_invoice
#             company_currency = inv.company_id.currency_id
# 
#             # create move lines (one per invoice line + eventual taxes and analytic lines)
#             iml = inv.invoice_line_move_line_get()
# #             iml += inv.tax_line_move_line_get()
# 
#             diff_currency = inv.currency_id != company_currency
#             # create one move line for the total and possibly adjust the other lines amount
#             total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)
#             
#             # amount penalty for vendor bill
#             currency = inv.currency_id.with_context(date=inv.date_invoice or fields.Date.context_today(self))
#             if inv.currency_id != company_currency:
#                 total_currency_amount_penalty = currency.round(inv.amount_penalty)
#                 price_amount_penalty = currency.compute(inv.amount_penalty, company_currency)
#             else:
#                 total_currency_amount_penalty = False
#                 price_amount_penalty = inv.currency_id.round(inv.amount_penalty)
#                 
#             total -= price_amount_penalty
#             total_currency -= total_currency_amount_penalty
#             
#             company_id = self._context.get('company_id', False)
#             if company_id:
#                 company_id = self.env['res.company'].browse(company_id)
#             else:
#                 company_id = self.env.user.company_id
#             
#             if inv.amount_penalty < 0:
#                 if not company_id.penalty_account_id:
#                     raise UserError('The Penalty Account for company ' + company_id.name + ' was not set yet. Please contact system administrator to configure it.')
#                 
#                 iml.append({
#                     'type': 'src',
#                     'name': 'Denda',
#                     'price': price_amount_penalty,
#                     'account_id': company_id.penalty_account_id.id,
#                     'date_maturity': inv.date_due,
#                     'amount_currency': diff_currency and total_currency_amount_penalty,
#                     'currency_id': diff_currency and inv.currency_id.id,
#                     'invoice_id': inv.id
#                 })
#             ########################################
# 
#             name = inv.name or '/'
#             if inv.payment_term_id:
#                 totlines = inv.with_context(ctx).payment_term_id.with_context(currency_id=inv.currency_id.id).compute(total, date_invoice)[0]
#                 res_amount_currency = total_currency
#                 ctx['date'] = date_invoice
#                 for i, t in enumerate(totlines):
#                     if inv.currency_id != company_currency:
#                         amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
#                     else:
#                         amount_currency = False
# 
#                     # last line: add the diff
#                     res_amount_currency -= amount_currency or 0
#                     if i + 1 == len(totlines):
#                         amount_currency += res_amount_currency
# 
#                     iml.append({
#                         'type': 'dest',
#                         'name': name,
#                         'price': t[1],
#                         'account_id': inv.account_id.id,
#                         'date_maturity': t[0],
#                         'amount_currency': diff_currency and amount_currency,
#                         'currency_id': diff_currency and inv.currency_id.id,
#                         'invoice_id': inv.id
#                     })
#             else:
#                 iml.append({
#                     'type': 'dest',
#                     'name': name,
#                     'price': total,
#                     'account_id': inv.account_id.id,
#                     'date_maturity': inv.date_due,
#                     'amount_currency': diff_currency and total_currency,
#                     'currency_id': diff_currency and inv.currency_id.id,
#                     'invoice_id': inv.id
#                 })
#             part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
#             line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
#             line = inv.group_lines(iml, line)
# 
#             journal = inv.journal_id.with_context(ctx)
#             line = inv.finalize_invoice_move_lines(line)
# 
#             date = inv.date or date_invoice
#             move_vals = {
#                 'ref': inv.reference,
#                 'line_ids': line,
#                 'journal_id': journal.id,
#                 'date': date,
#                 'narration': inv.comment,
#             }
#             ctx['company_id'] = inv.company_id.id
#             ctx['dont_create_taxes'] = True
#             ctx['invoice'] = inv
#             ctx_nolang = ctx.copy()
#             ctx_nolang.pop('lang', None)
#             move = account_move.with_context(ctx_nolang).create(move_vals)
#             # Pass invoice in context in method post: used if you want to get the same
#             # account move reference when creating the same invoice after a cancelled one:
#             move.post()
#             # make the invoice point to that move
#             vals = {
#                 'move_id': move.id,
#                 'date': date,
#                 'move_name': move.name,
#             }
#             inv.with_context(ctx).write(vals)
#         return True
    
    @api.multi
    def get_max_array(self):
        for this in self:
            count_inv = float(len(this.invoice_line_ids))
            count_inv = int(math.ceil(count_inv/10))
            count_denda = float(len(this.penalty_ids))
            count_denda = int(math.ceil(count_denda/4))
            this.max_array = max(count_inv,count_denda)
    
    max_array = fields.Integer('Max Array', compute='get_max_array')
    
    def get_rows(self):
        count = 1
        rows = list()
        cols = list()
        for item in self.invoice_line_ids:
            vals = {'code': item.product_id.default_code,
                    'name': item.product_id.name,
                    'description' : item.product_id.description_purchase,
                    'qty': item.quantity,
                    'uom': item.uom_id.name,
                    'price_unit': item.price_unit,
                    'subtotal': item.price_subtotal}
            if count == 10:
                cols.append(vals)
                rows.append(cols)
                cols = list()
                count = 1
            else:
                cols.append(vals)
                count += 1
        if count > 0:
            for i in range(11-count):
                vals = {'code': '-',
                        'name': '-',
                        'description' :'-',
                        'qty': '-',
                        'uom': '',
                        'price_unit': '-',
                        'subtotal': '-'}
                cols.append(vals)
            rows.append(cols)
        # compare
        if len(rows) < self.max_array:
            for i in range(self.max_array-len(rows)):
                cols = list()
                for j in range(10):
                    vals = {'code': '-',
                            'name': '-',
                            'description' :'-',
                            'qty': '-',
                            'uom': '',
                            'price_unit': '-',
                            'subtotal': '-'}
                    cols.append(vals)
                rows.append(cols)
        return rows

    
    @api.multi
    def get_rows_denda(self):
        count = 1
        rows = list()
        cols = list()
        for item in self.penalty_ids:
            tgl_penyerahan = datetime.strftime(datetime.strptime(item.penalty_date, '%Y-%m-%d'), '%d-%m-%Y')
            vals = {'code': item.product_id.default_code,
                    'product': item.product_id.name,
                    'description': item.product_id.description_purchase,
                    'tgl_penyerahan': tgl_penyerahan,
                    'denda': item.amount}
            if count == 4:
                cols.append(vals)
                rows.append(cols)
                cols = list()
                count = 1
            else:
                cols.append(vals)
                count += 1
        if count > 0:
            for i in range(5-count):
                vals = {'code': '-',
                        'product': '-',
                        'description': '-',
                        'tgl_penyerahan': '-',
                        'denda': '-'}
                cols.append(vals)
            rows.append(cols)
        # compare
        if len(rows) < self.max_array:
            for i in range(self.max_array-len(rows)):
                cols = list()
                for j in range(4):
                    vals = {'code': '-',
                            'product': '-',
                            'description': '-',
                            'tgl_penyerahan': '-',
                            'denda': '-'}
                    cols.append(vals)
                rows.append(cols)
        return rows    
    
    @api.multi
    def get_number_po(self):
        for this in self:
            po_number = False
            for line in this.invoice_line_ids:
                po_number = line.purchase_id.name
                break
            return po_number
    
    @api.multi
    def get_date_po(self):
        for this in self:
            date_po = False
            for line in this.invoice_line_ids:
                date_po = line.purchase_id.date_order
                break
            date_order_format = datetime.strptime(date_po, '%Y-%m-%d %H:%M:%S')
            user = self.env.user
            tz = pytz.timezone(user.tz) if user.tz else pytz.utc
            date_result = pytz.utc.localize(date_order_format).astimezone(tz)
            return datetime.strftime(date_result, '%Y-%m-%d %H:%M:%S')
    
    @api.multi
    def get_schedule_date_po(self):
        for this in self:
            schedule_date_po = False
            for line in this.invoice_line_ids:
                schedule_date_po = line.purchase_id.date_planned
                break
            schedule_date_format = datetime.strptime(schedule_date_po, '%Y-%m-%d %H:%M:%S')
            user = self.env.user
            tz = pytz.timezone(user.tz) if user.tz else pytz.utc
            date_result = pytz.utc.localize(schedule_date_format).astimezone(tz)
            return datetime.strftime(date_result, '%Y-%m-%d %H:%M:%S')
    
    @api.multi
    def do_print_ntb_report(self):
        for this in self:
            report_obj = self.env['report']
            template = self._template_ntb_report
            report = report_obj._get_report_from_name(template)
            data = {}
            datas = {
                'ids': this.id,
                'model': report.model,
                'form': data,
            }
            
        return report_obj.get_action(self, template, data=datas)
    

class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"
    
    progress_percent = fields.Float('Progress (%)')
    
    @api.onchange('progress_percent')
    def onchange_progress_percent(self):
        self.quantity = self.purchase_line_id.product_qty * self.progress_percent / 100
            