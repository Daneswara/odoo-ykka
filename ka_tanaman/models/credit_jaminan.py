from odoo import models, fields, api

class CreditJaminan(models.Model):
	_name = 'ka_plantation.credit.jaminan'


	name = fields.Char(string="No BPKB / No Sertifikat")
	jenis = fields.Selection([
		('bpkb',"BPKB"),
		('sertifikat',"Sertifikat")
		],string="Jenis Jaminan")
	tahun = fields.Integer(string="Tahun Pembuatan")
	luas = fields.Float(string="Luas Tanah")
	nilai = fields.Float(string="Taksiran Jaminan")
	credit_id = fields.Many2one('ka_plantation.credit.farmer')
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
	