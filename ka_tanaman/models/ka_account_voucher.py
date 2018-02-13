from odoo import models, fields, api, _

class ka_account_voucher(models.Model):
	_inherit = "ka_account.voucher"


	# credit_farmer_lines = fields.One2many('ka_plantation.credit.farmer','voucher_id',string="Credit Lines")
	@api.multi
	@api.model
	def posted_voucher(self):
		res = super(ka_account_voucher,self).posted_voucher()
		credit_id = self.env['ka_plantation.credit.farmer'].search([('voucher_id','=',self.id)])
		if credit_id:
			credit_id.state = 'paid'
			credit_id.date_paid = self.account_move_id.date
		return res

		