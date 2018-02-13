from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import pytz

class cash_flow_report_wizard(models.TransientModel):
    _name = "cash.flow.report.wizard"
    
    @api.model
    def default_get(self, fields):
        res = super(cash_flow_report_wizard, self).default_get(fields)
        user = self.env.user
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        datetime_now = datetime.now()
        datetime_now = pytz.utc.localize(datetime_now).astimezone(tz)
        first_day_of_year = datetime(datetime_now.year, 1, 1, 0, 0, 0)
        res['date_from'] = datetime.strftime(first_day_of_year, '%Y-%m-%d')
        res['date_to'] = datetime.strftime(datetime_now, '%Y-%m-%d')
        return res
    
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    
    @api.multi
    def generate_pdf_cash_flow_report(self):
        if self.date_from > self.date_to:
            raise UserError('Date To should be greater than Date From')
        
        report_obj = self.env['report']
        template = 'ka_account.template_ka_cash_flow_report'
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


class cash_flow_report_qweb(models.AbstractModel):
    _name = 'report.ka_account.template_ka_cash_flow_report'
    _template = 'ka_account.template_ka_cash_flow_report'

    def get_balance_move_lines(self, account_types, date_from, date_to):
        res = []
        for account_type in account_types:
            self._cr.execute('''select sum(move_line.balance) from account_move_line move_line
                                join account_account account on move_line.account_id = account.id
                                join account_account_type account_type on account.user_type_id = account_type.id
                                where account_type.name = %s and date >= %s and date <= %s''', (account_type, date_from, date_to))
            sum_balance = self._cr.fetchone()[0] or 0.0
            data = {'name': account_type, 'amount': sum_balance}
            res.append(data)
        return res

    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        docargs = {
            'data': data['form'],
            'get_balance_move_lines': self.get_balance_move_lines,
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
        }
        return report_obj.render(self._template, docargs)
    