from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
import pytz
from pygments.lexer import _inherit

class ka_general_ledger(models.TransientModel):
    _name = "ka_daily.cash" 
    
    name = fields.Char('Name', default='LAPORAN KAS HARIAN')
    report_date = fields.Date('Tanggal', default=fields.Date.context_today, required=True)
    
    
    @api.multi
    def generate_pdf_daily_cash(self):
        report_obj = self.env['report']
        template = 'ka_account.template_report_daily_cash'
        report = report_obj._get_report_from_name(template)
        domain = {
            'report_date': self.report_date
                }
        values = {
            'ids': self.ids,
            'model': report.model,
            'form': domain
                }
        
        return report_obj.get_action(self, template, data=values)
    
 
class daily_cash_qweb(models.AbstractModel):
    _name = 'report.ka_account.template_report_daily_cash'
    _template = 'ka_account.template_report_daily_cash'
    
    def get_company(self):
        return self.env.user.company_id.name
    
    def get_journal(self):
        journal_src = self.env['account.journal']
        journal_obj = journal_src.search([('type', 'in', ('bank','cash'))], order='type desc')
        return journal_obj    
    
    def get_voucher(self, move_id):
        voucher_src = self.env['ka_account.voucher']
        voucher_obj = voucher_src.search([('account_move_id','=', move_id)])
        return voucher_obj
    
    def get_opening_balance(self, journal_id, report_date):
        # compute starting balance
        debit_account = self.env['account.journal'].browse(journal_id).default_debit_account_id.id
        credit_account = self.env['account.journal'].browse(journal_id).default_credit_account_id.id
        self._cr.execute('select sum(debit) from account_move_line where date < %s and account_id = %s',
                         (report_date, debit_account))
        debit = self._cr.fetchone()[0] or 0
        self._cr.execute('select sum(credit) from account_move_line where date < %s and account_id = %s',
                         (report_date, credit_account))
        credit = self._cr.fetchone()[0] or 0
        res = debit - credit
        if res == 0:
            statement_src = self.env['account.bank.statement'].search([('journal_id','=',journal_id),('date','=',report_date)], limit=1)
            if statement_src:
                res = statement_src.balance_start
        return res
        
    def get_journal_item_penerimaan(self, report_date):
        account_ids = []
        journal_ids = []
        for journal in self.get_journal():
            journal_ids.append(journal.id)
            if journal.default_debit_account_id.id not in account_ids:
                account_ids.append(journal.default_debit_account_id.id)
        move_line_src = self.env['account.move.line']
        move_line_obj = move_line_src.search([('journal_id','in',journal_ids),
                                              ('account_id.user_type_id.id','=', 3),
                                              # ('account_id','not in',account_ids),
                                              ('date','=',report_date),
                                              ('debit','>', 0)
                                              ], order='move_id asc')
        return move_line_obj
    
    @api.multi
    def get_amount_penerimaan(self, journal_id, report_date):
        amount_penerimaan = 0
        move_line_obj = self.get_journal_item_penerimaan(report_date)
        for line in move_line_obj:
            if line.journal_id.id == journal_id:
                amount_penerimaan += line.debit
        return amount_penerimaan
            

    def get_journal_item_pengeluaran(self, report_date):
        account_ids = []
        journal_ids = []
        for journal in self.get_journal():
            journal_ids.append(journal.id)
            if journal.default_credit_account_id.id not in account_ids:
                account_ids.append(journal.default_credit_account_id.id)
        move_line_src = self.env['account.move.line']
        move_line_obj = move_line_src.search([('journal_id','in',journal_ids),
                                              ('account_id.user_type_id.id','=', 3),
                                              # ('account_id','not in',account_ids),
                                              ('date','=',report_date),
                                              ('credit','>', 0)], order='move_id asc')
        return move_line_obj
    
    def get_amount_pengeluaran(self, journal_id, report_date):
        amount_pengeluaran = 0
        move_line_obj = self.get_journal_item_pengeluaran(report_date)
        for line in move_line_obj:
            if line.journal_id.id == journal_id:
                amount_pengeluaran += line.credit
        return amount_pengeluaran
    
    def get_user(self):
        return self.env.user.name
    
    
    def get_print_date(self):
        user = self.env.user
        tz = pytz.timezone(user.tz)if user.tz else pytz.utc
        datetime_now = datetime.now()
        datetime_now = pytz.utc.localize(datetime_now).astimezone(tz)
        date_result = datetime.strftime(datetime_now, '%d-%m-%Y')
        return date_result
    
    def get_print_time(self):        
        user = self.env.user
        tz = pytz.timezone(user.tz)if user.tz else pytz.utc
        datetime_now = datetime.now()
        datetime_now = pytz.utc.localize(datetime_now).astimezone(tz)
        date_result = datetime.strftime(datetime_now, '%H:%M:%S')
        return date_result
    
    def get_company_city(self):
        return self.env.user.company_id.city

    def get_len_journal(self):
        len_journal = []
        for journal in self.get_journal():
            if journal.id not in len_journal:
                len_journal.append(journal.id)
        return len(len_journal)
    
    def total_td(self):
        len_journal = self.get_len_journal()
        total_td = 3 + len_journal
        return total_td
    
    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(data['ids'])
        docargs = {
            'data': data['form'],
            'get_company': self.get_company,
            'get_journal_item_penerimaan': self.get_journal_item_penerimaan,
            'get_journal':self.get_journal,
            'get_voucher':self.get_voucher,
            'get_opening_balance': self.get_opening_balance,
            'get_amount_penerimaan': self.get_amount_penerimaan,
            'get_journal_item_pengeluaran': self.get_journal_item_pengeluaran,
            'get_amount_pengeluaran': self.get_amount_pengeluaran,
            'get_print_date' : self.get_print_date,
            'get_print_time' : self.get_print_time,
            'get_user' : self.get_user,
            'get_company_city' : self.get_company_city,
            'total_td': self.total_td,
            'get_len_journal': self.get_len_journal,
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
        }
        return report_obj.render(self._template, docargs)
