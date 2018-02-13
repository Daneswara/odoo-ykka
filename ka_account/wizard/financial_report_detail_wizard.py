from odoo import models, fields, api, _
from datetime import datetime


class FinancialReportDetailWizard(models.TransientModel):
    _name = "financial.report.detail.wizard"
    
    date_from = fields.Date('Dari Tanggal')
    date_to = fields.Date('Sampai Tanggal')
    financial_report_id = fields.Many2one('account.financial.report', 'Account Report')
    line_ids = fields.One2many('financial.report.detail.wizard.line', 'wizard_id', 'Detail Lines')
    company_id = fields.Many2one('res.company', 'Company')
    
    
    def compute_value(self, account_id, date_from, date_to, is_cashflow):
        open_balance = debit = credit = 0.0
        if is_cashflow == True:
            self._cr.execute('''select sum(move_line.balance) from account_move_line move_line
                                join account_account account on move_line.account_id = account.id
                                join account_journal journal on move_line.journal_id = journal.id
                                where move_line.account_id = %s and move_line.date < %s 
                                and journal.type in ('cash','bank')''', (account_id, date_from))
            open_balance = self._cr.fetchone()[0] or 0.0
            
            self._cr.execute('''select sum(move_line.debit) from account_move_line move_line
                                join account_account account on move_line.account_id = account.id
                                join account_journal journal on move_line.journal_id = journal.id
                                where move_line.account_id = %s and move_line.date >= %s and move_line.date <= %s
                                and journal.type in ('cash','bank')''', (account_id, date_from, date_to))
            debit = self._cr.fetchone()[0] or 0.0
            
            self._cr.execute('''select sum(move_line.credit) from account_move_line move_line
                                join account_account account on move_line.account_id = account.id
                                join account_journal journal on move_line.journal_id = journal.id
                                where move_line.account_id = %s and move_line.date >= %s and move_line.date <= %s
                                and journal.type in ('cash','bank')''', (account_id, date_from, date_to))
            credit = self._cr.fetchone()[0] or 0.0
            
        else:
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
            
        return {'open_balance': open_balance,
                'debit': debit,
                'credit': credit,
                'end_balance': open_balance + debit - credit}
    
    @api.model
    def create(self, vals):
        account_report = vals.get('financial_report_id',False)
        company_id = vals.get('company_id',False)
        account_report_id = self.env['account.financial.report'].browse(account_report)
        line_vals = []
        if account_report_id.type == 'accounts':
            for account in account_report_id.account_ids:
                if not company_id or account.company_id.id == company_id or account.company_id.parent_id.id == company_id:
                    value = self.compute_value(account.id, vals.get('date_from'), vals.get('date_to'), account_report_id.is_cashflow)
                    line_vals.append((0,0,{'name': account.id,
                                           'open_balance': value.get('open_balance'),
                                           'debit': value.get('debit'),
                                           'credit': value.get('credit'),
                                           'end_balance': value.get('end_balance')}))
        elif account_report_id.type == 'account_type':
            account_type_ids = [account_type.id for account_type in account_report_id.account_type_ids]
            account_src = self.env['account.account'].search([('user_type_id','in',account_type_ids)])
            if company_id:
                account_src = self.env['account.account'].search([('user_type_id','in',account_type_ids),('company_id','child_of',company_id)])
            for account in account_src:
                value = self.compute_value(account.id, vals.get('date_from'), vals.get('date_to'), account_report_id.is_cashflow)
                line_vals.append((0,0,{'name': account.id,
                                       'open_balance': value.get('open_balance'),
                                       'debit': value.get('debit'),
                                       'credit': value.get('credit'),
                                       'end_balance': value.get('end_balance')}))
        vals['line_ids'] = line_vals
        return super(FinancialReportDetailWizard,self).create(vals)
    
    
class FinancialReportDetailWizardLine(models.TransientModel):
    _name = "financial.report.detail.wizard.line"
    
    wizard_id = fields.Many2one('financial.report.detail.wizard', 'Wizard')
    name = fields.Many2one('account.account', 'Account')
    open_balance = fields.Float('Saldo Awal')
    debit = fields.Float('Debit')
    credit = fields.Float('Kredit')
    end_balance = fields.Float('Saldo Akhir')
    
    @api.multi
    def action_show_general_ledger_from_account(self):
        for this in self:
            data = self.env['ka_general.ledger'].create({'account_id': this.name.id,
                                                         'date_from': this.wizard_id.date_from,
                                                         'date_to': this.wizard_id.date_to,
                                                         })
            data.with_context(is_cashflow=this.wizard_id.financial_report_id.is_cashflow).action_show_general_ledger()
            
            return {
                'name': _('Buku Besar'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'ka_general.ledger',
                'target': 'new',
                'res_id': data.id,
                'flags': {'form': {"initial_mode": "view",}},
            }  
    
