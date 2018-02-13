# -*- coding: utf-8 -*-
"""
 * Copyright Cak Juice 2016
 * untuk Nerita - Kebon Agung..
 * Gaween sakkarepmu..
"""

import time, datetime, calendar
from odoo import fields, api, models, _
from operator import itemgetter
import requests

global_account_report_custom = []

class BaseReportFinancialCustom(models.AbstractModel):
    _name = 'base_report_financial_custom'

    _report_name = None
    _report_vals = None

    def _compute_account_balance(self, accounts, cashflow_type=None):
        """ compute the balance, debit and credit for the provided accounts
        """
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }
        sql_cashflow = """(
            SELECT  company_id,
                journal_id,
                account_id, 
                to_date('{0}', 'YYYY-MM-DD') AS date, 
                SUM(debit) AS debit, sum(credit) AS credit,
                'ob' AS type
                FROM account_move_line  
                WHERE date < '{0}'
                GROUP BY 1, 2, 3
            UNION ALL
            SELECT  company_id,
                journal_id,
                account_id, 
                date, 
                0.0 as debit, sum(credit) as debit,
                'in' AS type
                FROM account_move_line 
                WHERE debit=0 AND date >='{0}' AND date <= '{1}' 
                AND account_id not in(select id from account_account where internal_type='liquidity') 
                GROUP BY  1, 2, 3, 4
            UNION ALL
            SELECT  company_id,
                journal_id,
                account_id, 
                date, 
                SUM(debit) AS debit, 0.0 AS credit,
                'out' AS type
                FROM account_move_line 
                WHERE credit=0 AND date >= '{0}' AND date <= '{1}' 
                AND account_id not in(select id from account_account where internal_type='liquidity') 
                GROUP BY  1, 2, 3, 4
            UNION ALL
            SELECT  company_id,
                journal_id,
                account_id, 
                date, 
                SUM(debit) AS debit, sum(credit) AS credit,
                'bl' AS type
                FROM account_move_line 
                WHERE date >= '{0}' AND date <= '{1}' 
                AND account_id not in(select id from account_account where internal_type='liquidity') 
                GROUP BY  1, 2, 3, 4) as cashflow""".format(self._context.get('date_from', False),
                                                     self._context.get('date_to', False))
        res = {}
        for account in accounts:
            res[account.id] = dict((fn, 0.0) for fn in mapping.keys())
        if accounts:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line"
            report_cashflow = self._context.get('financial_report_type', False) == 'cashflow'                
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            
            #spesific for cashflow report
            if report_cashflow:
                tables = sql_cashflow
                if cashflow_type:
                    filters = filters + " AND type = '%s' "%cashflow_type
                filters = filters.replace('account_move_line', 'cashflow')
                
            request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
                       " FROM " + tables + \
                       " WHERE account_id IN %s " \
                            + filters + \
                       " GROUP BY account_id"
            params = (tuple(accounts._ids),) + tuple(where_params) 
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res

    def _compute_report_balance(self, reports):
        # returns a dictionary with key = the ID of a record and value = the credit, debit and balance amount
        # computed for this record. If the record is of type :
        # 'accounts' : it's the sum of the linked accounts
        # 'account_type' : it's the sum of leaf accoutns with such an account_type
        # 'account_report' : it's the amount of the related report
        # 'sum' : it's the sum of the children of this record (aka a 'view' record)
        res = {}
        fields = ['credit', 'debit', 'balance']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                # it's the sum of the linked accounts
                res[report.id]['account'] = self._compute_account_balance(report.account_ids, report.cashflow_type)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                accounts = self.env['account.account'].search([('user_type_id', 'in', report.account_type_ids.ids)])
                res[report.id]['account'] = self._compute_account_balance(accounts, report.cashflow_type)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                res2 = self._compute_report_balance(report.account_report_id)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
        return res
        
    def get_account_lines(self, data):
        lines = []
        account_report = self.env['account.financial.report'].search([('id', '=', data['account_report_id'][0])])
        child_reports = account_report._get_children_by_order()
        res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports)
        if data['enable_filter']:
            comparison_res = self.with_context(data.get('comparison_context'))._compute_report_balance(child_reports)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in comparison_res[report_id].get('account').items():
                        report_acc[account_id]['comp_bal'] = val['balance']

        for report in child_reports:
            vals = {
                'company_id': self.env.user.company_id.id,
                'sequence': report.sequence,
                'name': report.name,
                'id': report.id,
                'balance': res[report.id]['balance'] * report.sign,
                # 'type': 'report',
                'type':report.type,
                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                'account_type': report.type or False, #used to underline the financial report balances
                'display_value': report.display_value,
            }
            if data['debit_credit']:
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']

            if data['enable_filter']:
                vals['balance_cmp'] = res[report.id]['comp_bal'] * report.sign

            lines.append(vals)
            if report.display_detail == 'no_detail':
                #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                continue

            if res[report.id].get('account'):
                sub_lines = []
                for account_id, value in res[report.id]['account'].items():
                    #if there are accounts to display, we add them to the lines with a level equals to their level in
                    #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                    #financial reports for Assets, liabilities...)
                    flag = False
                    account = self.env['account.account'].browse(account_id)
                    vals = {
                        'company_id': self.env.user.company_id.id,
                        'sequence': report.sequence,
                        'name': account.code + ' ' + account.name,
                        'balance': value['balance'] * report.sign or 0.0,
                        'type': 'account',
                        'level': report.display_detail == 'detail_with_hierarchy' and 4,
                        'account_type': account.internal_type,
                    }
                    if data['debit_credit']:
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if not account.company_id.currency_id.is_zero(vals['debit']) or not account.company_id.currency_id.is_zero(vals['credit']):
                            flag = True
                    if not account.company_id.currency_id.is_zero(vals['balance']):
                        flag = True
                    if data['enable_filter']:
                        vals['balance_cmp'] = value['comp_bal'] * report.sign
                        if not account.company_id.currency_id.is_zero(vals['balance_cmp']):
                            flag = True
                    if flag:
                        sub_lines.append(vals)
                lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
        return lines
    
    def _get_periode(self, month, year):
        date_from = None
        date_to = None
        m = month
        y = year

        if m == 0:
            date_from = datetime.date(y, 1, 1)
            date_to = datetime.date(y, 12, calendar.monthrange(y, 12)[1])
        else:
            date_from = datetime.date(y, m, 1)
            date_to = datetime.date(y, m, calendar.monthrange(y, m)[1])
            
        return (date_from, date_to)
        
    def _generate_pivote_data(self, data):
        ldata = len(data)
        idx = 0
        res = []
        while idx < ldata:
            row = data[idx]
            key = row['sequence']
            last_key = key
            col = 0
            total_balance = 0
            while last_key == key:
                col = col + 1
                total_balance = total_balance + data[idx]['balance']
                row['balance_%s' % col] = data[idx]['balance']
                idx = idx + 1
                if idx == ldata:
                    break
                key = data[idx]['sequence']
            del row['company_id']
            row['balance'] = total_balance
            res.append(row)
        return res

    def _prepare_report_data(self, report_type, report_id, date_from, date_to, company_ids):
        docs = []
        if report_type == 'cashflow':
            journal_ids=[j.id for j in self.env['account.journal'].search([('type', 'in', ('cash', 'bank'))])]
        else:
             journal_ids=[j.id for j in self.env['account.journal'].search([])]

        for c in self.env['res.company'].browse(map(int, company_ids)):
            user_id = c.get_internal_user()
            wizard = self.env['accounting.report']
            rec = wizard.sudo(user_id).create({
                'enable_filter': False,
                'account_report_id': report_id,
                'debit_credit': False,
                'date_from': date_from,
                'date_to': date_to,
                'target_move': 'all',
                'journal_ids': [(4,[journal_ids])],
            })
            
            report = rec.sudo(user_id).check_report()
            report['data']['form']['used_context']['financial_report_type'] = report_type
            doc = self.sudo(user_id).get_account_lines(report['data']['form'])
            docs = docs + doc
        return rec, report, docs
     
    def _get_opening_balance(self, report_type, report_id, date_from, company_ids):
        date_to = date_from - datetime.timedelta(days=1)
        return self._prepare_report_data(report_type, report_id, None, date_to, company_ids)

    def _get_balance(self, report_type, report_id, date_to, company_ids):
        return self._prepare_report_data(report_type, report_id, None, date_to, company_ids)

    def _get_periode_balance(self, report_type, report_id, date_from, date_to, company_ids):
        return self._prepare_report_data(report_type, report_id, date_from, date_to, company_ids)
          
    @api.model
    def get_financial_report(self, model_name, report_type, report_id, month, year, company):
        # 0 -> Consolidation
        # 1 -> Main company

        report_data = []
        column_header = []
        date_from, date_to = self._get_periode(month, year)
        if company == 0:
            companies = self.env['res.company'].search([])
        else:
            companies = self.env['res.company'].browse(company)

        company_ids = [c.id for c in companies]
        company_names = [c.name for c in companies]
        cname = company_names[0] if len(company_names) == 1 else 'KONSOLIDASI'

        # if len(company_ids) == 1:
            # rec, form, report_data = self._get_opening_balance(report_type, report_id, date_from, company_ids)
        # rec, form, current_balance = self._get_periode_balance(report_type, report_id, date_from, date_to, company_ids)
        
        if report_type in ('profitloss', 'balancesheet_horizontal', 'balancesheet_vertical', 'arus_kas'):
            if len(company_ids) == 1:
                rec, form, report_data = self._get_opening_balance(report_type, report_id, date_from, company_ids)
            rec, form, current_balance = self._get_periode_balance(report_type, report_id, date_from, date_to, company_ids)
        else: #cash flow
            prev_date_to =  date_from - datetime.timedelta(days=1)
            prev_date_from = prev_date_to.replace(day=1)
            rec, form, report_data = self._get_periode_balance(report_type, report_id, prev_date_from, prev_date_to, company_ids)
            rec, form, current_balance = self._get_periode_balance(report_type, report_id, date_from, date_to, company_ids)

        report_data = report_data + current_balance        
        report_data = sorted(report_data, key=itemgetter('sequence', 'company_id'))
        pivote = self._generate_pivote_data(report_data)
        # for l in pivote:
            # print l['sequence'], l['level'],  l['type'], l['name'], l['balance_1'], l['balance_2']
            
        _data = form['data']['form']
        _data.update({'company_name': cname})
        _data.update({'financial_report_type': report_type})
        vals = {
            'doc_ids': [rec.id],
            'doc_model': model_name,
            'data': _data,
            'docs': rec,
            'time': time,
            'get_account_lines': pivote,
        }

        return rec.id, vals

    @api.model
    def get_html_financial_report(self, model_name, report_type, report_id, month, year, company):
        rec_id, vals = self.get_financial_report(model_name, report_type, report_id, month, year, company)
        return self.env['report'].render(self._report_name, vals)

    @api.model
    def get_pdf_financial_report(self, model_name, report_type, report_id, month, year, company):
        rec_id, vals = self.get_financial_report(model_name, report_type, report_id, month, year, company)
        global global_account_report_custom

        global_account_report_custom.append({
            'uid': self.env.uid,
            'vals': vals
        })

        return self.env['report'].get_action([rec_id], self._report_name)

    @api.model
    def render_html(self, docids, data=None):
        global global_account_report_custom

        is_exists = False
        idx = 0
        temp_vals = None
        for g in global_account_report_custom:
            if g['uid'] == self.env.uid:
                is_exists = True
                temp_vals = g['vals']
                break
            idx += 1

        if is_exists:
            del global_account_report_custom[idx]

        return self.env['report'].render(self._report_name, temp_vals)

class ReportFinancialPortrait(models.AbstractModel):
    _name = 'report.ka_account.report_financial_portrait_view'
    _inherit = 'base_report_financial_custom'

    _report_name = 'ka_account.report_financial_portrait_view'
    _report_vals = None

class ReportFinancialLandscape(models.AbstractModel):
    _name = 'report.ka_account.report_financial_landscape_view'
    _inherit = 'base_report_financial_custom'

    _report_name = 'ka_account.report_financial_landscape_view'
    _report_vals = None