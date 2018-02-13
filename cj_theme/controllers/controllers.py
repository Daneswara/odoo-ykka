# -*- coding: utf-8 -*-
from odoo import http
import time

class CjTheme(http.Controller):
	@http.route('/cj_theme/cj_theme/<data>', type='http', auth='user')
	def index(self, data=None, **kw):
		model = 'report.account.report_financial';
		results = http.request.env[model].get_report()
		items = ''
		for result in results:
			items += '<p>' + result['name'] + '</p>'
		return '<div>' + items + '</div>'
		# wizard = http.request.env['accounting.report'].create({
		# 	'enable_filter': False,
		# 	'account_report_id': 9,
		# 	'debit_credit': False,
		# })

		# report = wizard.check_report()

		# value = {
		# 	'doc_ids': 1,
		# 	'doc_model': 'accounting.report',
		# 	'data': report['data']['form'],
		# 	'docs': 46,
		# 	'time': time,
		# 	'get_account_lines': http.request.env['report.account.report_financial'].get_account_lines(report['data']['form']),
		# }

		# report_obj = http.request.env['report']
		# context = dict(http.request.env.context)
		# html = report_obj.with_context(context).get_html(value['doc_ids'], 'account.report_financial', value['get_account_lines'])
		# print html
		# return http.request.make_response(html)

		#print wizard.check_report()
		# return http.request.render('account.report_financial', value)
		#return get_html()

	
	{
		'report_file': u'account.report_financial',
		'context': {
			'lang': u'en_US',
			'active_ids': [56],
			'tz': False,
			'uid': 1
		},
		'data': {
			'model': 'ir.ui.menu',
			'ids': [],
			'form': {
				'comparison_context': {
					'state': u'posted',
					'journal_ids': [31, 19, 13, 25, 26, 20, 14, 32, 21, 27, 15, 33, 16, 34, 28, 22, 30, 24, 36, 18, 35, 17, 23, 29, 37, 39, 40, 38]
				},
				'filter_cmp': u'filter_no',
				'date_from': False,
				'enable_filter': False,
				'journal_ids': [31, 19, 13, 25, 26, 20, 14, 32, 21, 27, 15, 33, 16, 34, 28, 22, 30, 24, 36, 18, 35, 17, 23, 29, 37, 39, 40, 38],
				'date_to_cmp': False,
				'used_context': {
					'lang': u'en_US',
					'state': u'posted',
					'strict_range': False,
					'date_to': False,
					'date_from': False,
					'journal_ids': [31, 19, 13, 25, 26, 20, 14, 32, 21, 27, 15, 33, 16, 34, 28, 22, 30, 24, 36, 18, 35, 17, 23, 29, 37, 39, 40, 38]
				}, 'date_from_cmp': False,
				'debit_credit': False,
				'date_to': False,
				'label_filter': False,
				'account_report_id': (9, u'Laba Rugi - Perbiaya'),
				'id': 56,
				'target_move': u'posted'
			}
		},
		'report_name': u'account.report_financial',
		'report_type': u'qweb-html',
		'type': 'ir.actions.report.xml',
		'name': u'Financial report'
	}

    # @http.route('/cj_theme/cj_theme/objects/', auth='public')
    # def list(self, **kw):
    #     return http.request.render('cj_theme.listing', {
    #         'root': '/cj_theme/cj_theme',
    #         'objects': http.request.env['cj_theme.cj_theme'].search([]),
    #     })

    # @http.route('/cj_theme/cj_theme/objects/<model("cj_theme.cj_theme"):obj>/', auth='public')
    # def object(self, obj, **kw):
    #     return http.request.render('cj_theme.object', {
    #         'object': obj
    #     })