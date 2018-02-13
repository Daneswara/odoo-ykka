from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from calendar import monthrange


class ka_trial_balance_report_wizard(models.TransientModel):
    _name = "ka_trial.balance.report.wizard"
    
    @api.model
    def default_get(self, fields):
        res = super(ka_trial_balance_report_wizard, self).default_get(fields)
        # default financial report
        report_src = self.env['account.financial.report'].search([('name','=','NERACA BULANAN')])
        if report_src:
            res['account_report_id'] = report_src.id
        # default date
        year = datetime.now().year
        month = datetime.now().month
        last_day = monthrange(year, month)[1]
        res['date_from'] = datetime.strftime(datetime(year, month, 1), '%Y-%m-%d')
        res['date_to'] = datetime.strftime(datetime(year, month, last_day), '%Y-%m-%d')
        return res
    
    account_report_id = fields.Many2one('account.financial.report', 'Financial Report', required=True)
    date_from = fields.Date('Dari Tanggal', required=True)
    date_to = fields.Date('Sampai Tanggal', required=True)
    file_type = fields.Selection([('pdf','PDF'),('xlsx','Excel')], 'Format File', default='pdf', required=True)
    
    @api.onchange('date_from')
    def onchange_date_from(self):
        if self.date_from:
            date_from = datetime.strptime(self.date_from, '%Y-%m-%d')
            year = date_from.year
            month = date_from.month
            last_day = monthrange(year, month)[1]
            self.date_to = datetime.strftime(datetime(year, month, last_day), '%Y-%m-%d')
    
    @api.multi
    def generate_pdf_trial_balance_report(self):
        if self.date_from > self.date_to:
            raise UserError('Date To should be greater than Date From')
        
        report_obj = self.env['report']
        template = 'ka_account.ka_trial_balance_report_tmpl'
        report = report_obj._get_report_from_name(template)
        domain = {
            'account_report_id': self.account_report_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        values = {
            'ids': self.ids,
            'model': report.model,
            'form': domain
        }
        return report_obj.get_action(self, template, data=values)
    
    @api.multi
    def generate_xlsx_trial_balance_report(self):
        return self.env['report'].get_action(self, 'trial.balance.xlsx')


class ka_trial_balance_report_qweb(models.AbstractModel):
    _name = 'report.ka_account.ka_trial_balance_report_tmpl'
    _template = 'ka_account.ka_trial_balance_report_tmpl'

    def get_trial_balance_data(self, account_report_id):
        return self.env['account.financial.report'].search([('parent_id','=',account_report_id)], order='sequence asc')
    
    def get_amount(self, account_id, date_from, date_to):
        self._cr.execute('''select sum(move_line.balance) from account_move_line move_line
                            join account_account account on move_line.account_id = account.id
                            where account_id = %s and date < %s''', (account_id, date_from))
        open_balance = self._cr.fetchone()[0] or 0.0
        
        self._cr.execute('''select sum(move_line.debit) from account_move_line move_line
                            join account_account account on move_line.account_id = account.id
                            where account_id = %s and date >= %s and date <= %s''', (account_id, date_from, date_to))
        debit = self._cr.fetchone()[0] or 0.0
        
        self._cr.execute('''select sum(move_line.credit) from account_move_line move_line
                            join account_account account on move_line.account_id = account.id
                            where account_id = %s and date >= %s and date <= %s''', (account_id, date_from, date_to))
        credit = self._cr.fetchone()[0] or 0.0
        
        res = {'open_balance': open_balance,
               'debit': debit,
               'credit': credit,
               'end_balance': open_balance + debit - credit}
        return res

    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        docargs = {
            'data': data['form'],
            'get_trial_balance_data': self.get_trial_balance_data,
            'get_amount': self.get_amount,
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
        }
        return report_obj.render(self._template, docargs)


