from odoo import models, fields, api
# from odoo.addons.ka_rest_api.models.models import PushModel

# class res_provinsi(PushModel):
class res_provinsi(models.Model):
	_name = 'res.provinsi'

	code = fields.Char(string="Kode", size=1, required=True)
	name = fields.Char(string="Nama Provinsi", required=True, size=128)
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)

	_sql_constraints = [
		('res_provinsi_code_company_unique', 'unique(code, company_id)', 'Dalam satu Unit/PG kode provinsi tidak boleh sama!'),
	]

	# _push_fields = ['code', 'name']

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