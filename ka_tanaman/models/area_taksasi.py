from odoo import models, fields, api

class AreaTaksasi(models.Model):
	_name = 'ka_plantation.area.taksasi'
	_rec_name = 'register_id'

	register_id = fields.Many2one('ka_plantation.register', string="No. Register", required=True)
	periode_id = fields.Many2one('ka_plantation.periode', string="Periode", required=True)
	taksasi = fields.Float(string="Ton Tebu/Hektar", required=True)