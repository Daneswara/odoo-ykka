
from odoo import models, fields, api

class FingerspotUser(models.Model):
	_name = 'ka_fingerspot.user'
	_description = "FingerSport User PIN"

	pin = fields.Char(string="No. Pin",size=16,index=True)
	name = fields.Char(string="Nama",size=32)
	password = fields.Char(string="Password",size=32)
	rfid = fields.Char(string="Kode RFID",size=32)
	privilege = fields.Integer(string="Hak Akses")
	template_lines = fields.One2many('ka_fingerspot.user.template','user_pin_id',string="Data Scan")

	@api.multi
	def name_get(self):
		res = []
		for s in self:
			pin = s.pin or  ''
			name = s.name or ''
			res.append((s.id, pin + ' - ' + name))
		return res

	# @override
	@api.model
	def name_search(self, name='', args=None, operator='ilike', limit=80):
		if not args:
			args = []

		if name:
			record = self.search([('pin', operator, name)] + args, limit=limit)
			if not record:
				record = self.search([('name', operator, name)] + args, limit=limit)
		else:
			record = self.search(args, limit=limit)

		return record.name_get()

class FingerspotUserTemplate(models.Model):
	_name = 'ka_fingerspot.user.template'
	_description = "FingerSport User Template"

	user_pin_id = fields.Many2one('ka_fingerspot.user',string="User")
	index = fields.Integer(string="Index")
	alg_version = fields.Integer(string="Versi Algoritma")
	template = fields.Binary(string="Binary Scan")		