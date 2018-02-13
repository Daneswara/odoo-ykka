from odoo import models, fields, api

class CreditTraktor(models.Model):
	_name = 'ka_plantation.credit.traktor'
	_inherits = {'ka_plantation.credit.farmer': 'credit_id'}

	# kud_id = fields.Many2one(related='farmer_id.kud_id')
	credit_id = fields.Many2one('ka_plantation.credit.farmer', required=True, ondelete='cascade')
	petani_telp = fields.Many2one()
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
	
