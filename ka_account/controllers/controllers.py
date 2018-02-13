import time
from odoo import models, fields, api
from odoo.http import Controller, route, request
        
class AccountFinancialReport(Controller):

    @route('/finance_report/<int:report_id>/', type='http', auth='user')
    def get_financial_report(self, report_id, data=None, **kw):
        wizard = request.env['accounting.report']
        rec = wizard.create({
            'enable_filter': False,
            'account_report_id': report_id,
            'debit_credit': False,
        })
        report = rec.check_report()
        vals = {
			'doc_ids': [rec.id],
			'doc_model': 'accounting.report',
			'data': report['data']['form'],
			'docs': rec,
			'time': time,
			'get_account_lines': request.env['report.account.report_financial'].get_account_lines(report['data']['form']),
		}
        #return request.env['report'].get_action(rec, 'ka_account.report_financial', vals)
        return request.env['report'].render('ka_account.report_financial', vals)