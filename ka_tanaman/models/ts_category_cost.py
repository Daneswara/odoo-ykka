from odoo import models, fields, api

class TsCategoryCost(models.Model):
	_name = 'ka_plantation.ts.category.cost'
	_order = 'code'

	code = fields.Char(string="Kode", size=24, required=True)
	name = fields.Char(string="Nama", required=True)
	category_id = fields.Many2one('ka_plantation.ts.category', string="Kategori TS", required=True)
	property_account_id = fields.Many2one('account.account', string="Perkiraan Biaya", company_depend=True, required=True)
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)

	_sql_constraints = [
		('ts_category_cost_code_unique', 'UNIQUE(code)', 'Kode sudah ada, silahkan masukkan kode lain!')
	]

	# @override
	@api.multi
	def name_get(self):
		res = []
		for s in self:
			code = s.code or ''
			name = s.name or ''
			res.append((s.id, code + ' - ' + name))

		return res

	# @override
	@api.model
	def name_search(self, name='', args=None, operator='ilike', limit=80):
		if not args:
			args = []

		if name:
			record = self.search([('code', operator, name)] + args, limit=limit)
			if not record:
				record = self.search([('name', operator, name)] + args, limit=limit)
		else:
			record = self.search(args, limit=limit)

		return record.name_get()