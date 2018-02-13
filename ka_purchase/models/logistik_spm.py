from odoo import models, fields

class logistik_spm(models.Model):
	_inherit = 'logistik.spm'

	sp_ids = fields.One2many('purchase.order', 'spm_id', string='Realisasi SP', readonly=True)