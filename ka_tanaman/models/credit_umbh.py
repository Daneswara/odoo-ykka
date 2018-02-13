from odoo import models, fields, api

class CreditUmbh(models.Model):
	_name = 'ka_plantation.credit.umbh'
	_inherits = {'ka_plantation.credit.farmer': 'credit_id'}

	credit_id = fields.Many2one('ka_plantation.credit.farmer', required=True, ondelete='cascade')
	pekerjaan = fields.Char(string="Pekerjaan Petani")
	taks_rendemen = fields.Float(string="Rendemen (%)")
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
	