from odoo import models, fields

class account_analytic_account(models.Model):
	_inherit = 'account.analytic.account'

	sp_ids = fields.One2many('purchase.order.line', 'account_analytic_id', string='Realisasi SP', readonly=True)