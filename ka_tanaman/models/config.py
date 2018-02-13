from odoo import models, fields, api

class Configure(models.Model):
	_name = 'ka_plantation.configure'

	api_key = fields.Char(string="API Key",store=True,required=True)
	petak_valid = fields.Char(string="Petak Valid",required=True)
	petak_invalid = fields.Char(string="Petak Invalid",required=True)
	petak_rehab = fields.Char(string="Petak Rehabilitasi",required=True)
	tgl_buat = fields.Date(string="Tanggal",default=lambda self: fields.datetime.now())
	created_by = fields.Many2one('res.users', string="Dibuat oleh", default= lambda self: self.env.user.id,readonly=True)
	