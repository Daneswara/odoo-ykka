from odoo import models, fields


class AreaIntersect(models.TransientModel):
	_name = 'ka_plantation.area.intersect'

	name = fields.Text(string="kode intersection",readonly=True)
	
	def reload(self):
		return{
			'type': 'ir.actions.client',
    		'tag': 'reload',
		}