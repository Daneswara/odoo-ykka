# -*- coding: utf-8 -*-
from openerp.osv import expression
from openerp import models, fields, api

class AccountAccountTemplate(models.Model):
    _inherit = "account.account.template"
   
    parent_id = fields.Many2one("account.account.template", string="Parent Account", ondelete='cascade', domain=[('user_type_id','=','View')])
    child_ids = fields.One2many("account.account.template", "parent_id", string="Children")
    company_ids = fields.Many2many(comodel_name='res.company',
                relation='account_template_company_rel',
                column1='account_id',
                column2='company_id', string='Unit/PG' )
    display_unit = fields.Char(compute="_display_unit", string="Unit/PG", size=10)
               
    @api.one
    @api.depends("company_ids") 
    def _display_unit(self):
        res = [unit.code for unit in self.company_ids]
        self.display_unit = '-'.join(res)
            
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        accounts = self.search(domain + args, limit=limit)
        return accounts.name_get()

        
class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

   	
    @api.multi
    def generate_account(self, tax_template_ref, acc_template_ref, code_digits, company):
        """ This method for generating accounts from templates.

            :param tax_template_ref: Taxes templates reference for write taxes_id in account_account.
            :param acc_template_ref: dictionary with the mappping between the account templates and the real accounts.
            :param code_digits: number of digits got from wizard.multi.charts.accounts, this is use for account code.
            :param company_id: company_id selected from wizard.multi.charts.accounts.
            :returns: return acc_template_ref for reference purpose.
            :rtype: dict
        """        
        self.ensure_one()
        account_tmpl_obj = self.env['account.account.template']
        acc_template = account_tmpl_obj.search([('nocreate', '!=', True), ('chart_template_id', '=', self.id)], order='id')
        for account_template in acc_template:
            if account_template.user_type_id.type == 'view':
                continue
            tax_ids = []
            for tax in account_template.tax_ids:
                tax_ids.append(tax_template_ref[tax.id])

            # code_main = account_template.code and len(account_template.code) or 0
            # code_acc = account_template.code or ''
            # if code_main > 0 and code_main <= code_digits:
                # code_acc = str(code_acc) + (str('0'*(code_digits-code_main)))
            company_ids = [c.id for c in account_template.company_ids] + [1]
            
            if company.id not in company_ids:
                continue
                
            code_acc = account_template.code.replace("U", company.code)
            vals = {
				'account_template_id': account_template.id,
                'name': account_template.name,
                'currency_id': account_template.currency_id and account_template.currency_id.id or False,
                'code': code_acc,
                'user_type_id': account_template.user_type_id and account_template.user_type_id.id or False,
                'reconcile': account_template.reconcile,
                'note': account_template.note,
                'tax_ids': [(6, 0, tax_ids)],
                'company_id': company.id,
                'tag_ids': [(6, 0, [t.id for t in account_template.tag_ids])],
            }
            new_account = self.env['account.account'].create(vals)
            acc_template_ref[account_template.id] = new_account.id
        return acc_template_ref	