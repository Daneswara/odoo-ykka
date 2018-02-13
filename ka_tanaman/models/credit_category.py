from odoo import models, fields, api

class CreditCategory(models.Model):
	_name = 'ka_plantation.credit.category'

	code = fields.Char(string="Kode",digits=2)
	name = fields.Char(string="Nama",digits=30)
	property_account_id = fields.Many2one('account.account',company_dependent=True,string="No. Perkiraan")
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
	 