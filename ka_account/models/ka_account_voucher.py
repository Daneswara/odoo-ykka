from odoo import models, fields, api, _
import urllib2
import time
import math
import datetime
from dbfpy import dbf
from odoo.exceptions import UserError
from openerp.addons.amount_to_text_id.amount_to_text import Terbilang
from odoo.tools.misc import formatLang


class ka_account_voucher(models.Model):
    _name = "ka_account.voucher"        
    _description = "Account Voucher for Kebon Agung"
    _inherit = ['mail.thread']
    _order = "date_approve asc"
        
        
    name = fields.Char("Nomor", default="/", copy=False) 
    journal_id = fields.Many2one("account.journal", string="Journal")
    destination_journal_id = fields.Many2one("account.journal", string="Tujuan")
    description = fields.Char("Keperluan")
    partner_id = fields.Many2one("res.partner", string="Rekanan", required=True)
    partner_name = fields.Char("Nama Rekanan")
    date = fields.Date("Tanggal", default=fields.Date.context_today)
    state = fields.Selection([("draft", "Draft"),
                              ("proposed", "Proposed"),
                              ("approved", "Approved"),
                              ("posted", "Posted")],
                                string = "Status", default="draft", track_visibility="always", copy=False)
    type = fields.Selection([("inbound", "Penerimaan Kas"),
                             ("outbound", "Pengeluaran Kas"),
                             ("internal", "Internal Transfer"),
                             ("intercompany", "Intercompany")], string = "Type")
    account_move_id = fields.Many2one("account.move", string="Journal Entry", copy=False)
    voucher_lines = fields.One2many("ka_account.voucher.line", "ka_voucher_id", string="Payment Line", copy=True)
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.user.company_id.currency_id)
    total_amount = fields.Monetary("Total", compute="compute_amount")
    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get('ka_account.voucher'))
    operating_unit_id = fields.Many2one("res.partner", "Unit/PG")
    printed = fields.Boolean("Printed", copy=False)
    ka_payment_ids = fields.One2many('ka_account.payment', 'journal_voucher_id', string='Payments')
    confirmed_payment_id = fields.Many2one('ka_account.payment.confirm', 'Confirmed Payment')
    partner_bank_id = fields.Many2one('res.partner.bank', string='Bank')
    partner_bank_acc = fields.Char(string='No. Acc')
    main_state = fields.Selection([('draft', 'Draft'),('confirm', 'Confirmed')], related='confirmed_payment_id.state')
    journal_entry_info = fields.Char('Journal Entry Info', compute='get_journal_entry_info')
    status_export = fields.Boolean("Status Export",default=False)
    date_approve = fields.Datetime('Approval Date', copy=False)
    account_id = fields.Many2one('account.account', 'Account', related='voucher_lines.account_id')
    

    @api.onchange('partner_bank_id')
    def onchange_partner_bank_id(self):
        self.partner_bank_acc = self.partner_bank_id.acc_number
    
    @api.onchange('operating_unit_id')
    def onchange_operating_unit_id(self):
        if self.type == 'intercompany':
            self.partner_id = self.operating_unit_id.id
            
    @api.onchange('destination_journal_id')
    def onchange_destination_journal_id(self):
        if self.type == 'internal':
            self.partner_bank_acc = self.destination_journal_id.bank_acc_number
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        bank = self.env['res.partner.bank'].search([('partner_id','=',self.partner_id.id)], order="priority asc, id desc", limit=1)
        self.partner_bank_id = bank.id
        self.partner_name = self.partner_id.name
    
    @api.model
    @api.depends('account_move_id')
    def get_journal_entry_info(self):
        for this in self:
            this.journal_entry_info = '-'
            if this.account_move_id:
                this.journal_entry_info = this.account_move_id.name + ' ' + this.account_move_id.date
    
    @api.multi
    def action_delete(self):
        for this in self:
            this.write({'confirmed_payment_id': False})
        return True
    
    
    @api.depends('voucher_lines.amount')
    def compute_amount(self):
        for this in self:
            total_amount = 0.0
            for payment in this.voucher_lines:
                total_amount += payment.amount
            this.total_amount = total_amount

    @api.multi
    def unlink(self):
        for this in self:
            if this.state != 'draft':
                raise UserError('Sorry, you cannot delete non-draft voucher.')
        return super(ka_account_voucher, self).unlink()

    @api.multi
    def action_view_vendor_payments(self):
        for this in self:
            domain = [('id', 'in', [x.id for x in self.env['ka_account.payment'].search([('journal_voucher_id','=', this.id)])])]

            return {
                'name': 'Vendor Payments',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'domain' : domain,
                'type': 'ir.actions.act_window',
                'res_model': 'ka_account.payment',
                'target': 'current',  
            }

    @api.multi
    def propose_voucher(self):
        for this in self:
            vals = {'state': 'proposed'}
            if this.name == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code("ka_account.voucher")
            this.write(vals)
        return True
    
    @api.multi
    def approve_voucher(self):
        for this in self:
            date_approve = datetime.datetime.now()
            date_approve.strftime("%Y-%m-%d %H:%M:%S")
            this.write({'state': 'approved', 'date_approve': date_approve})
    
    @api.multi
    def set_draft_voucher(self):
        for this in self:
            statement_line_id = self.env['account.bank.statement.line'].search([('journal_voucher_id.id','=', this.id)])
            if statement_line_id.journal_entry_ids:
                raise UserError("Sorry, you cannot set to draft because the bank/cash statement line related to this voucher is already reconciled.")

            proposal = self.env['ka_account.payment.confirm'].browse(this.confirmed_payment_id.id)
            if proposal.state == 'confirm':
                raise UserError('Sorry you can not set this voucher to draft because it already proposed to bank.')
            else:
                this.write({
                    'state': 'draft', 
                    'printed': False,
                    'confirmed_payment_id': False})
        return True

    @api.multi
    def posted_voucher(self, posted_date=None):
        for this in self:
            line_items = []
            data_entry = {}
            if not posted_date or isinstance(posted_date, dict):
                posted_date = this.date
                
            if not posted_date:
                posted_date = datetime.datetime.now()
                posted_date.strftime("%Y-%m-%d")
            acc_move_obj = this.env['account.move']
            
            if this.type == "inbound":
                account = this.journal_id.default_debit_account_id.id
                val_one = {
                    'account_id': account,
                    'partner_id': this.partner_id.id,
                    'name': this.description,
                    'debit': this.total_amount,
                    'journal_id': this.journal_id.id    
                }  
                line_items.append((0, 0, val_one))
                
                for line in this.voucher_lines:
                    credit = 0
                    debit = 0
                    name = str(line.name)
                    if line.invoice_id:
                        name = str(line.invoice_id.number) +' - '+ name
                    journal = line.ka_voucher_id.journal_id.id
                    if line.amount > 0:
                        credit = abs(line.amount)
                    elif line.amount < 0:
                        debit = abs(line.amount)
              
                    vals = {
                        'account_id': line.account_id.id,
                        'partner_id': this.partner_id.id,
                        'name': name,
                        'analytic_account_id':line.analytic_account_id.id,
                        'debit': debit,
                        'credit': credit,
                        'journal_id': journal,
                        'reconcile_invoice_id': line.invoice_id.id or False
                    }
                    line_items.append((0, 0, vals))
                line_items.reverse()
            
            elif this.type in ('outbound', 'internal', 'intercompany'):
                account = this.journal_id.default_credit_account_id.id
                val_one = {
                    'account_id': account,
                    'partner_id': this.partner_id.id,
                    'name': this.description,
                    'credit': this.total_amount,
                    'journal_id': this.journal_id.id    
                }  
                line_items.append((0, 0, val_one))
                
                for line in this.voucher_lines:
                    credit = 0
                    debit = 0
                    name = str(line.name)
                    if line.invoice_id:
                        name = str(line.invoice_id.number) +' - '+ name
                    journal = line.ka_voucher_id.journal_id.id
                    if line.amount < 0:
                        credit = abs(line.amount)
                    elif line.amount > 0:
                        debit = abs(line.amount)
              
                    vals = {
                        'account_id': line.account_id.id,
                        'partner_id': this.partner_id.id,
                        'name': name,
                        'analytic_account_id': line.analytic_account_id.id,
                        'debit': debit,
                        'credit': credit,
                        'journal_id': journal,
                        'reconcile_invoice_id': line.invoice_id.id or False
                    }    
                    line_items.append((0, 0, vals))
                line_items.reverse()
    
            data_entry = {
                'ka_voucher_id' : this.id,
                'journal_id': this.journal_id.id,
                'ref': this.name,
                'date':posted_date,
                'line_ids': line_items
            }
            
            this.state = 'posted'   
            acc_move_create = acc_move_obj.create(data_entry)
            acc_move_create.post()  
            this.write({'account_move_id': acc_move_create.id})  
            
            if this.type == 'internal':
                this.copy({'type': 'inbound',
                           'journal_id': this.destination_journal_id.id,
                           'destination_journal_id': False})
            
            if this.type == 'intercompany':
                this.copy_kas_masuk()
            
            # change status payments become paid                    
            for payment in this.ka_payment_ids:
                payment.write({'state': 'paid', 'date_paid': posted_date})
                
            # PROCESS RECONCILIATION
            for move_line in this.account_move_id.line_ids:
                if move_line.reconcile_invoice_id:
                    move_lines_to_reconcile = [move_line.id]
                    move_line_src = self.env['account.move.line'].search([('move_id','=',move_line.reconcile_invoice_id.move_id.id),
                                                                          ('account_id','=',move_line.account_id.id)])
                    for move_line_res in move_line_src:
                        move_lines_to_reconcile.append(move_line_res.id)
                    self.env['account.move.line'].browse(move_lines_to_reconcile).reconcile()
                    
                # reconcile bail payment
                default_bail_account_id = self.env.user.company_id.default_bail_account_id.id
                if move_line.account_id.id == default_bail_account_id and not move_line.reconciled and move_line.debit > 0:
                    move_lines_to_reconcile = [move_line.id]
                    for voucher_line in this.voucher_lines:
                        payment_with_bail_src = self.env['ka_account.payment'].search([('invoice_id','=',voucher_line.ka_payment_id.invoice_id.id),
                                                                                       ('is_bail_payment','=',False),
                                                                                       ('amount_bail','>',0),
                                                                                       ('state','=','paid')])
                        for payment_with_bail in payment_with_bail_src:
                            for move_line_res in payment_with_bail.journal_voucher_id.account_move_id.line_ids:
                                if not move_line_res.reconciled and move_line_res.account_id.id == move_line.account_id.id and move_line_res.id not in move_lines_to_reconcile and move_line_res.credit > 0:
                                    move_lines_to_reconcile.append(move_line_res.id)
                    self.env['account.move.line'].browse(move_lines_to_reconcile).reconcile()
        
    
    @api.multi
    def copy_kas_masuk(self):
        for this in self:
            source_uid = self.env.user.company_id.intercompany_user_id.id
            ou_company = this.sudo(source_uid).operating_unit_id.get_company_ref()[0]
            partner_id = self.env.user.company_id.partner_id
            account_payable_unit = partner_id.sudo(ou_company.internal_user_id.id).with_context(company_id=ou_company.id).property_account_payable_id.id
            
            default = {
                       'journal_id' : False,
                       'name' : this.name,
                       'partner_id': partner_id.id,
                       'type' : 'inbound',
                       'company_id': ou_company.id,
                       'printed' : False,
                       'voucher_lines' : None,
            }
            
            copy_kas_masuk = self.sudo(source_uid).copy(default=default)
            line_non_bank_cash = []
            for line in this.voucher_lines:
                if line.account_template_id.user_type_id.name == 'Bank and Cash': 
                    account = self.env['account.account'].sudo(source_uid).with_context(company_id=ou_company.id).search([('account_template_id', '=', line.account_template_id.id),
                                                                                                                          ('company_id', '=', ou_company.id)])
                    journal_src = self.sudo(ou_company.internal_user_id.id).with_context(company_id=ou_company.id).env['account.journal'].search([('default_debit_account_id','=',account.id)], limit=1)
                    
                    if journal_src:
                        copy_kas_masuk.write({'journal_id' : journal_src.id})
                        
                    default_line = {
                        'ka_voucher_id': copy_kas_masuk.id,
                        'account_id': account_payable_unit,
                    }
                    
                    line.sudo(source_uid).copy(default=default_line)
                
                else:
                    line_non_bank_cash.append(line.id)
            
            if len(line_non_bank_cash) > 0:
                acc_move_obj = this.env['account.move']
                line_items = []
                data_entry = {}
                total_debit = 0.0
                for line in self.env['ka_account.voucher.line'].browse(line_non_bank_cash):
                    credit = 0
                    debit = abs(line.amount)
                    total_debit += debit
                    account_template = self.env['account.account'].sudo(source_uid).with_context(company_id=ou_company.id).search([('account_template_id', '=', line.account_template_id.id),('company_id', '=', ou_company.id )],limit=1)    

                    vals = {
                            'account_id': account_template.id,
                            'partner_id': this.partner_id.id,
                            'name': line.name,
                            'analytic_account_id': line.analytic_account_id.id,
                            'debit': debit,
                            'credit': credit,
                            }    
                    line_items.append((0, 0, vals))
                    # print "line iteems", line_items
                
                val_one = {
                            'account_id': account_payable_unit,
                            'partner_id': this.partner_id.id,
                            'name': this.description,
                            'credit': total_debit,
                            }  
                line_items.append((0, 0, val_one))
                
                journal = self.env['account.journal'].sudo(source_uid).with_context(company_id=ou_company.id).search([('type', '=', 'general'),('company_id', '=', ou_company.id )],limit=1)           
                data_entry = {
                            'journal_id': journal.id,
                            'ref': this.name,
                            'date':this.date,
                            'line_ids': line_items
                            }
                this.state = 'posted'   
                acc_move_create = acc_move_obj.sudo(source_uid).with_context(company_id=ou_company.id).create(data_entry)
                      
            if len(copy_kas_masuk.voucher_lines) == 0:
                copy_kas_masuk.unlink()
                
    @api.multi
    def unposted_voucher(self):
        for this in self:
            statement_src = self.env['account.bank.statement.line'].search([('journal_voucher_id','=',this.id)])
            if statement_src:
                for statement in statement_src:
                    statement.button_cancel_reconciliation()
            else:
                this.account_move_id.line_ids.remove_move_reconcile()
                this.account_move_id.button_cancel()
                this.account_move_id.unlink()
                this.write({'state': 'approved'})
                    
    @api.multi
    def action_view_journal_entry(self):
        for this in self:
            return {
                'name': 'Journal Entry',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id' : this.account_move_id.id,
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'target': 'current',  
            }
       
    @api.multi
    def mark_printed_document(self):
        for this in self:
            if this.printed != True:
                vals = {'printed': True}
                this.write(vals)
    
    @api.multi
    def get_max_array(self):
        for this in self:
            count_lines = float(len(this.voucher_lines))
            count_lines = int(math.ceil(count_lines/10))
            this.max_array = count_lines
    max_array = fields.Integer('Max Array', compute='get_max_array')

    def get_rows(self, type=None):
        count = 1
        rows = list()
        cols = list()
        for item in self.voucher_lines:
            uraian = ''
            if item.invoice_id.number :
                uraian = item.invoice_id.number+' - '+item.name
            else :
                uraian = item.name

            vals = {
                'account_id': item.account_id.code,
                'uraian': uraian,
                'amount': item.amount
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
            for i in range(11-count):
                vals = {
                    'account_id': '',
                    'uraian': '',
                    'amount': ''
                }
                cols.append(vals)
            rows.append(cols)
        return rows
    
    @api.multi
    def get_max_array_plus(self):
        for this in self:
            count_lines = float(len(this.voucher_lines))
            count_lines = int(math.ceil(count_lines/35))
            this.max_arrayp = count_lines
    
    max_arrayp = fields.Integer('Max Array', compute='get_max_array_plus')

    def get_rows_plus(self):
        count = 1
        rows = list()
        cols = list()
        for item in self.voucher_lines:
            uraian = ''
            if item.invoice_id.number :
                uraian = item.invoice_id.number+' - '+item.name
            else :
                uraian = item.name

            vals = {
                'account_id': item.account_id.code,
                'uraian': uraian,
                'amount': item.amount
            }
            if count == 44:
                cols.append(vals)
                rows.append(cols)
                cols = list()
                count = 1
            else:
                cols.append(vals)
                count += 1
        if count > 0:
            for i in range(45-count):
                vals = {
                    'account_id': '',
                    'uraian': '',
                    'amount': ''
                }
                cols.append(vals)
            rows.append(cols)
        return rows

    def amount_to_text_id(self, amount):
        return Terbilang(amount) + " Rupiah"

    def process_voucher_reconciliation_move_link(self, statement_line_id, posted_date=None):
        self.posted_voucher(posted_date)
        self.account_move_id.statement_line_id = statement_line_id.id
        for move_line in self.account_move_id.line_ids:
            move_line.write({'statement_id': statement_line_id.statement_id.id})
    
    def open_export_dbf_wizard(self):
        return {
            'name':'Export ke BUKTIAU1',
            'type':'ir.actions.act_window',
            'res_model':'ka_account.export.buktiaua1.wizard',
            'target': 'new',  
            'view_type':'form',
            'view_mode':'form',
            }
    @api.multi
    def export_to_dbf(self):
        bari  = 1
        list_nobu= []
        db = dbf.Dbf("/var/lib/odoo/work/AKUNTING/2017/BUKTIAU1.DBF")
 
        for a in db:
            cek = a['NOBU'][:3]
            if cek == 'PB-':
                temp = a['NOBU'][3:]
                list_nobu.append(int(temp))
 
        nobu = max(list_nobu)+1
        if nobu <99:
            nobu = 'PB-00'+str(nobu)
        elif nobu <999:
            nobu = 'PB-0'+str(nobu)
        elif nobu <9999:
            nobu = 'PB-'+str(nobu)
 
        rec = db.newRecord()
        rec["KD_TRANS"] = 'K'
        rec["PERK"] = self.journal_id.default_debit_account_id.code
        rec["SUBP"] = self.partner_id.code
        rec["NOBU"] = nobu
        rec["NOBU_LAMA"] = ''
        rec["BARI"] = bari
        rec["URAI"] = self.partner_id.name
        rec["JUML"] = -self.total_amount
        rec["TANDA"] = ''
        rec["TGL_MAINT"] = self.date[:4]+self.date[5:7]+self.date[8:]
        rec["USR_MAINT"] = self.env.user.name
        rec.store()
 
        for s in self.voucher_lines:
            bari += 1
            rec = db.newRecord()
            rec["KD_TRANS"] = 'K'
            rec["PERK"] = s.account_id.code
            rec["SUBP"] = self.partner_id.code
            rec["NOBU"] = nobu
            rec["NOBU_LAMA"] = ''
            rec["BARI"] = bari
            rec["URAI"] = s.name
            rec["JUML"] = s.amount
            rec["TANDA"] = ''
            rec["TGL_MAINT"] = self.date[:4]+self.date[5:7]+self.date[8:]
            rec["USR_MAINT"] = self.env.user.name
            rec.store()    
         
        # for a in db:
            # print a
 
        db.close()
        self.status_export =  True
            
        
class ka_account_voucher_line(models.Model):
    _name = "ka_account.voucher.line"
    _description = "Account Voucher Line for Kebon Agung"
    
    name = fields.Char ("Keterangan")
    account_id = fields.Many2one("account.account", string="Account")
    account_template_id = fields.Many2one("account.account.template", string="Account Template")
    invoice_id = fields.Many2one("account.invoice", string="Invoice")
    amount = fields.Monetary("Amount")
    ka_voucher_id = fields.Many2one("ka_account.voucher", string="Account Payment")
    currency_id = fields.Many2one("res.currency", "Currency", default=lambda self: self.env.user.company_id.currency_id)
    analytic_account_id = fields.Many2one("account.analytic.account", string="Analytic Account")
    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, 
        default=lambda self: self.env['res.company']._company_default_get('ka_account.voucher.line'))
    ka_payment_id = fields.Many2one('ka_account.payment', 'Payment')
    
    
    @api.model
    def default_get(self, fields):
        res = super(ka_account_voucher_line, self).default_get(fields)
        operation_unit = self._context.get('op_unit')
        unit = self.env['res.partner'].browse(operation_unit)
        if self._context.get('type') != 'internal':
            default_account = unit.property_account_receivable_id.id
        else:
            default_account = self.env.user.company_id.default_account_internal_transfer.id
        res['name'] = self._context.get('desc')
        res['account_id'] = default_account
        
        return res
    
    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        self.amount = self.invoice_id.residual
        
    def prepare_voucher_lines_for_reconciliation_widget(self, target_currency=False, target_date=False):
        context = dict(self._context or {})
        ret = []
        for line in self:
            company_currency = line.account_id.company_id.currency_id
            debit = 0
            credit = 0
            amount = line.amount if line.ka_voucher_id.type in ('outbound', 'intercompany') else -line.amount
            amount_str = formatLang(self.env, amount, currency_obj=company_currency)
            invoice_name = '' if not line.invoice_id else ' - ' + line.invoice_id.number
            if line.ka_voucher_id.type == 'inbound':
                if line.amount < 0:
                    credit = abs(line.amount)
                else:
                    debit = abs(line.amount)

            if line.ka_voucher_id.type in ('outbound', 'internal', 'intercompany'):
                if line.amount < 0:
                    debit = abs(line.amount)
                else:
                    credit = abs(line.amount)
                    
            data = {
                'account_type': u'payable', 
                'amount_currency_str': '', 
                'currency_id': False, 
                'date_maturity': target_date, 
                'date': line.ka_voucher_id.date, 
                'total_amount_str': amount_str, 
                'partner_id': line.ka_voucher_id.partner_id.id, 
                'account_name': line.account_id.name, 
                'name': line.name + invoice_name,
                'partner_name': line.ka_voucher_id.partner_name or line.ka_voucher_id.partner_id.name, 
                'total_amount_currency_str': '', 
                'credit': credit, 
                'journal_name': u'Vendor Bills', 
                'amount_str': amount_str, 
                'debit': debit, 
                'account_code': line.account_id.code, 
                'ref': '', 
                'counterpart_aml_id': False,
                'already_paid': False
            }
            ret.append(data)
        return ret          
