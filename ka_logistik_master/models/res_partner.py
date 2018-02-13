from odoo import models, fields, api

class res_partner(models.Model):
	_inherit = 'res.partner'

	#Disable Translation
	name = fields.Char(string='Tag Name', required=True, translate=False)

	code = fields.Char(string='Kode', size=10)
	alias = fields.Char(string='Singkatan', size=12)
	kelompok = fields.Char(string='Kelompok', size=20)
	bidang_usaha = fields.Char(string='Bidang Usaha', size=35)
	no_npwp = fields.Char(string='No. NPWP', size=20)
	bank = fields.Char(string='Nama Bank', size=30)
	no_acc = fields.Char(string='Nomor ACC', size=20)
	is_calon = fields.Boolean(string='Calon Rekanan', default=False)
	tgl_anggota = fields.Date(string='Tgl. Anggota')

	_sql_constraints = [('code_unique', 'unique(code,company_id,is_company)', 'Kode rekanan tidak boleh dobel!'),]

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

	@api.one
	def action_convert_partner(self):
		code = self.code.replace('-X', '')
		return self.write({'is_calon': False, 'code': code})

	@api.one
	def action_convert_calon_partner(self):
		code = self.code + '-X'
		return self.write({'is_calon': True, 'code': code})