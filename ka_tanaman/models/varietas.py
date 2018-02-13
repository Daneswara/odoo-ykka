from odoo import models, fields, api

class Varietas(models.Model):
	_name = 'ka_plantation.varietas'
	_order = 'code'

	code = fields.Char(string="Kode", size=2, required=True)
	name = fields.Char(string="Nama", required=True)
	masak_category = fields.Selection([('awal','Masak Awal'),('tengah','Masak Tengah'),('akhir','Masak Akhir')],string="Kategori Masak",required=True,store=True)


	_sql_constraints = [
		('ts_category_code_unique', 'UNIQUE(code)', 'Kode sudah ada, silahkan masukkan kode lain!')
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