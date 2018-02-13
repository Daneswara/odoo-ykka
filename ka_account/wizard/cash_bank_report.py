from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from openerp.addons.amount_to_text_id.amount_to_text import Terbilang

class CashBankReport(models.TransientModel):
    _name = 'cash.bank.report'
    
    name = fields.Char('Name', default='LAPORAN KAS / BANK')
    report_date = fields.Date('Tanggal', default=fields.Date.context_today, required=True)
    
    @api.multi
    def generate_pdf_cash_bank(self):
        report_obj = self.env['report']
        template = 'ka_account.template_report_cash_bank'
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
    
    
class CashBankReportQweb(models.AbstractModel):
    _name = 'report.ka_account.template_report_cash_bank'
    _template = 'ka_account.template_report_cash_bank'
     
    
    def get_user(self):
        return self.env.user.name
    
    def get_company(self):
        return self.env.user.company_id.name
    
    def get_company_city(self):
        return self.env.user.company_id.city
    
    def get_journal(self):
        journal_src = self.env['account.journal']
        journal_obj = journal_src.search([('type', 'in', ('bank','cash'))], order='type desc')
        return journal_obj
    
    def get_journal_item_penerimaan(self, report_date, j_id):
        line_obj =self.env['account.bank.statement.line']
        statement_lines = line_obj.search([('date','=',report_date),
                                           ('journal_id','=', j_id),
                                           ('amount','>',0)])
        return statement_lines
    
    def get_journal_item_pengeluaran(self, report_date, j_id):
        line_obj =self.env['account.bank.statement.line']
        statement_lines = line_obj.search([('date','=',report_date),
                                           ('journal_id','=', j_id),
                                           ('amount','<',0)])
        return statement_lines
    
    def get_rows1(self, report_date):
        rows = list()
        for j in self.get_journal():
            line_penerimaan = self.get_journal_item_penerimaan(report_date, j.id)
            line_pengeluaran = self.get_journal_item_pengeluaran(report_date, j.id)
            bank_statements = self.env['account.bank.statement'].search([('journal_id','=',j.id), ('date','=',report_date)])
                        
            vals = {
                'no_perk': j.default_debit_account_id.code,
                'perk': j.default_debit_account_id.name,
                'sum_penerimaan': sum(line.amount for line in line_penerimaan),
                'sum_pengeluaran': sum(line.amount for line in line_pengeluaran),
                'end_balance': sum(line.balance_end_real for line in bank_statements),
                
                }
            rows.append(vals)
        return rows
        
    def get_rincian_kas(self, report_date):
        cashbox = list()
        for j in self.get_journal():
            if j.type == 'cash':
                bank_statements = self.env['account.bank.statement'].search([('journal_id','=',j.id), ('date','=',report_date)])
                for bs in bank_statements:
                    for line in bs.cashbox_end_id.cashbox_lines_ids:
                        val = {
                            'is_cash': line.cash_nominal_id.is_cash,
                            'cash_nominal_id': line.cash_nominal_id.name,
                            'coin_value':line.coin_value,
                            'lbr_kasir': line.number_cashier,
                            'lbr_pbuku': line.number
                            }
                        cashbox.append(val)
        return cashbox
    
    def amount_to_text_id(self, amount):
        return Terbilang(amount) + " Rupiah"
                        
    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        docargs = {
            'data': data['form'],
            'get_user': self.get_user,
            'get_company': self.get_company,
            'get_company_city': self.get_company_city,
            'get_journal':self.get_journal,
            'get_rows1': self.get_rows1,
            'get_rincian_kas': self.get_rincian_kas,
            'amount_to_text_id': self.amount_to_text_id,
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
        }
        return report_obj.render(self._template, docargs)