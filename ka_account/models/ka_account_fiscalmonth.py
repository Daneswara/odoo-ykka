from odoo import models, fields

class ka_account_fiscalmonth(models.Model):
	_name = 'ka.account.fiscalmonth'
	_description = 'Fiscal Month'

	name = fields.Char(string="Nama Bulan", size=16, required=True)