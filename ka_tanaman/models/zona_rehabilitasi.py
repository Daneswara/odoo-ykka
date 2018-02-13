from odoo import models, fields, api

class ZonaRehabilitasi(models.Model):
	_name = 'ka_plantation.zona.rate'

	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
	name = fields.Char(string="Nama Zona")
	tarif = fields.Float(string="Tarif")
	desa_ids = fields.Many2many(comodel_name='res.desa.kelurahan',
		string="Zona Desa")