from odoo import models, fields, api

class CreditJadwal(models.Model):
	_name = 'ka_plantation.credit.jadwalkirimtebu'

	kuantum = fields.Float(string="Kuantum (ku)")
	tanggal = fields.Date(string="Tanggal",default=lambda self: fields.datetime.now())
	jumlah = fields.Float(string="Jumlah Tebu (ku)")
	tebang_periode_id = fields.Many2one('ka_plantation.register')
	credit_id = fields.Many2one('ka_plantation.credit.farmer')
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
	