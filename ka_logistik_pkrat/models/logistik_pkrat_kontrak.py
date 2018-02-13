from odoo import models, fields

class logistik_pkrat_kontrak(models.Model):
 	_name = 'logistik.pkrat.kontrak'
	_description = "PKRAT Kontrak"
	
	pkrat_id = fields.Many2one('logistik.pkrat', string='Nama Proyek')