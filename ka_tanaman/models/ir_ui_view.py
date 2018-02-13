from odoo import models, fields

class AreamapView(models.Model):
	_inherit = 'ir.ui.view'

	type = fields.Selection(selection_add=[
		('areamap', 'Areamap'),
		('arearehab', 'Arearehab'),
	])