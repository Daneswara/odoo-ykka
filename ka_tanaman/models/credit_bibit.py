from odoo import models, fields, api

class Creditbibit(models.Model):
	_name = 'ka_plantation.credit.bibit'
	# _inherits = {'ka_plantation.credit.farmer': 'credit_id'}

	varietas_id = fields.Many2one('ka_plantation.varietas')
	jumlah_bibit = fields.Integer(string="Jumlah Bibit(mata)")
	intensifikasi_id = fields.Many2one('ka_plantation.intensifikasi')
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
	