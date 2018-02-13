from odoo import models, fields, api

class res_dusun(models.Model):
	_name = 'res.dusun'

	code = fields.Char(string="Kode", size=5, required=True, readonly=True)
	code_urut = fields.Char(string="Kode Urutan", size=2, required=True)
	name = fields.Char(string="Nama Dusun", required=True, size=128)
	desa_kelurahan_id = fields.Many2one('res.desa.kelurahan',string="Nama Desa",required=True)
	kecamatan_id = fields.Many2one(string="Kecamatan", related='desa_kelurahan_id.kecamatan_id', readonly=True)
	kab_kota_id = fields.Many2one(string="Kabupaten / Kota", related='kecamatan_id.kab_kota_id', readonly=True)
	provinsi_id = fields.Many2one(string="Provinsi", related='kab_kota_id.provinsi_id', readonly=True)
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)

	_sql_constraints = [
		('res_dusun_code_company_unique', 'unique(code, company_id)', 'Dalam satu Unit/PG kode dusun tidak boleh sama!'),
	]

	def _set_code(self, desa_kelurahan, code_urut):
		return desa_kelurahan + code_urut

	@api.model
	def create(self, vals):
		_desa_kelurahan = (self.env['res.desa.kelurahan'].browse(vals['desa_kelurahan_id'])).code
		vals.update({'code': self._set_code(_desa_kelurahan, vals['code_urut'])})
		return super(res_dusun, self).create(vals)

	@api.multi
	def write(self, vals):
		_desa_kelurahan = (self.env['res.desa.kelurahan'].browse(vals['desa_kelurahan_id'])).code if vals.has_key('desa_kelurahan_id') else self.desa_kelurahan_id.code
		_code_urut = vals['code_urut'] if vals.has_key('code_urut') else self.code_urut
		vals.update({'code': self._set_code(_desa_kelurahan, _code_urut)})
		return super(res_dusun, self).write(vals)

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

	@api.onchange('desa_kelurahan_id', 'code_urut')
	def onchange_code(self):
		_desa_kelurahan = self.desa_kelurahan_id.code if self.desa_kelurahan_id else ''
		_code_urut = self.code_urut if self.code_urut else ''
		self.code = self._set_code(_desa_kelurahan, _code_urut)