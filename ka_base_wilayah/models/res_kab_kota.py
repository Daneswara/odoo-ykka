from odoo import models, fields, api

class res_kab_kota(models.Model):
	_name = 'res.kab.kota'

	code = fields.Char(string="Kode", size=1, required=True)
	name = fields.Char(string="Nama Kabupaten / Kota", required=True, size=128)
	provinsi_id = fields.Many2one('res.provinsi', string="Provinsi", required=True)
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
	kecamatan_ids = fields.One2many('res.kecamatan','kab_kota_id', string="Kecamatan")

	_sql_constraints = [
		('res_kab_kota_code_company_unique', 'unique(code, company_id)', 'Dalam satu Unit/PG kode kabupaten/kota tidak boleh sama!'),
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