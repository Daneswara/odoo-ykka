from odoo import models, fields, api

class account_analytic_account(models.Model):
	_inherit = "account.analytic.account"

	is_stasiun = fields.Boolean(string='Stasiun ?')
	analytic_type = fields.Selection([
		('view','Tampilan'),
		('normal','Normal'),
	], string='Type')
	stasiun_id = fields.Many2one('account.analytic.stasiun', string='Related Stasiun')
	operating_unit_id = fields.Many2one(related='company_id.partner_id', store=True, 
		domain=[('is_operating_unit', '=', True)], string="Unit/PG", readonly=True)

	# # @override
	# @api.multi
	# def name_get(self):
	# 	res = []
	# 	for s in self:
	# 		code = s.code or ''
	# 		name = s.name or ''
	# 		res.append((s.id, code + ' - ' + name))

	# 	return res

	# # @override
	# @api.multi
	# def name_search(self, name='', args=None, domain=[], operator='ilike', limit=80):
	# 	if not args:
	# 		args = []

	# 	if name:
	# 		record = self.search([('code', operator, name)] + args, limit=limit)
	# 		if not record:
	# 			record = self.search([('name', operator, name)] + args, limit=limit)
	# 	else:
	# 		record = self.search(args, limit=limit)

	# 	return record.name_get()