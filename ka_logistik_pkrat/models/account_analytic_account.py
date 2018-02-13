# ----------------------------------------------------------
# Data Account Analytic Account
# inherit 'account.analytic.account'
# ----------------------------------------------------------

from odoo import models, fields

class account_analytic_account(models.Model):
	_inherit = 'account.analytic.account'

	is_pkrat = fields.Boolean(string='PKRAT', default=True)
	pkrat_type = fields.Selection([
		('1','Investasi Baru'),#untuk initital G dan B 
		('2','Perbaikan Luar Biasa'),#untuk untial P
		('3','Inventaris'), #untuk initial I
	], string='Jenis Investasi')	