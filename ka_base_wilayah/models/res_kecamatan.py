from odoo import models, fields, api

class res_kecamatan(models.Model):
	_name = 'res.kecamatan'

	code = fields.Char(string="Kode", size=3, required=True, readonly=True)
	code_urut = fields.Char(string="Kode Urutan", size=2, required=True)
	name = fields.Char(string="Nama Kecamatan", required=True, size=128)
	kab_kota_id = fields.Many2one('res.kab.kota', string="Kabupaten / Kota", required=True)
	provinsi_id = fields.Many2one(string="Provinsi", related='kab_kota_id.provinsi_id', readonly=True)
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
	desa_ids = fields.One2many('res.desa.kelurahan','kecamatan_id', string="Desa")
	
	_sql_constraints = [
		('res_kecamatan_code_company_unique', 'unique(code, company_id)', 'Dalam satu Unit/PG kode kecamatan tidak boleh sama!'),
	]

	def _set_code(self, kab_kota, code_urut):
		return kab_kota + code_urut

	@api.model
	def create(self, vals):
		_kab_kota = (self.env['res.kab.kota'].browse(vals['kab_kota_id'])).code
		vals.update({'code': self._set_code(_kab_kota, vals['code_urut'])})
		return super(res_kecamatan, self).create(vals)

	@api.multi
	def write(self, vals):
		_kab_kota = (self.env['res.kab.kota'].browse(vals['kab_kota_id'])).code if vals.has_key('kab_kota_id') else self.kab_kota_id.code
		_code_urut = vals['code_urut'] if vals.has_key('code_urut') else self.code_urut
		vals.update({'code': self._set_code(_kab_kota, _code_urut)})
		return super(res_kecamatan, self).write(vals)

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

	@api.onchange('kab_kota_id', 'code_urut')
	def onchange_code(self):
		_kab_kota = self.kab_kota_id.code if self.kab_kota_id else ''
		_code_urut = self.code_urut if self.code_urut else ''
		self.code = self._set_code(_kab_kota, _code_urut)