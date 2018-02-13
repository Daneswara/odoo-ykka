from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from calendar import monthrange


class ka_trial_balance_report_wizard_old(models.TransientModel):
    _name = "ka_trial.balance.report.wizard_old"
    
    @api.model
    def default_get(self, fields):
        res = super(ka_trial_balance_report_wizard_old, self).default_get(fields)
        year = datetime.now().year
        month = datetime.now().month
        last_day = monthrange(year, month)[1]
        res['date_from'] = datetime.strftime(datetime(year, month, 1), '%Y-%m-%d')
        res['date_to'] = datetime.strftime(datetime(year, month, last_day), '%Y-%m-%d')
        return res
    
    date_from = fields.Date('Date From', required=True)
    date_to = fields.Date('Date To', required=True)
    
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
        template = 'ka_account.ka_trial_balance_report_tmpl_old'
        report = report_obj._get_report_from_name(template)
        domain = {
            'date_from': self.date_from,
            'date_to': self.date_to
        }
        values = {
            'ids': self.ids,
            'model': report.model,
            'form': domain
        }
        return report_obj.get_action(self, template, data=values)


class ka_trial_balance_report_qweb_old(models.AbstractModel):
    _name = 'report.ka_account.ka_trial_balance_report_tmpl_old'
    _template = 'ka_account.ka_trial_balance_report_tmpl_old'

    def get_trial_balance_data(self, date_from, date_to):
        res = []
        account_ids = self.env['account.account'].sudo().search([('company_id','=',self.env.user.company_id.id)], order='code asc')
        for account in account_ids:
            self._cr.execute('''select sum(move_line.balance) from account_move_line move_line
                                join account_account account on move_line.account_id = account.id
                                where account_id = %s and date < %s''', (account.id, date_from))
            opening_balance = self._cr.fetchone()[0] or 0.0
            
            self._cr.execute('''select sum(move_line.debit) from account_move_line move_line
                                join account_account account on move_line.account_id = account.id
                                where account_id = %s and date >= %s and date <= %s''', (account.id, date_from, date_to))
            debit = self._cr.fetchone()[0] or 0.0
            
            self._cr.execute('''select sum(move_line.credit) from account_move_line move_line
                                join account_account account on move_line.account_id = account.id
                                where account_id = %s and date >= %s and date <= %s''', (account.id, date_from, date_to))
            credit = self._cr.fetchone()[0] or 0.0
            
            data = {'parent_id': account.parent_id.id,
                    'parent_name': account.parent_id.name,
                    'account_code': account.code,
                    'account_name': account.name, 
                    'opening_balance': opening_balance,
                    'debit': debit,
                    'credit': credit,
                    'ending_balance': opening_balance + debit - credit}
            res.append(data)
        return res

    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        docargs = {
            'data': data['form'],
            'get_trial_balance_data': self.get_trial_balance_data,
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
        }
        return report_obj.render(self._template, docargs)
    