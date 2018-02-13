from odoo import models, fields, api

class FingerspotActionLog(models.Model):
	_name = 'ka_fingerspot.action.log'

	command = fields.Char(string="Aksi", size=64)
	date_action = fields.Datetime(string="Tanggal Aksi", default=fields.Datetime.now)
	log_message = fields.Text(string="Pesan")
	user_id = fields.Many2one('res.users', string="Perintah Oleh", default=lambda self: self.env.user.id)
	device_id = fields.Many2one('ka_fingerspot.device', string="Device")
	state = fields.Selection([
		("error", "Error"),
		("success", "Success")
	], string="State", default="error")

	# Override
	@api.multi
	def name_get(self):
		res = []
		for s in self:
			name = s.command or ''
			res.append((s.id, name))
		return res

	# Override
	@api.model
	def name_search(self, name='', args=None, operator='ilike', limit=80):
		if not args:
			args = []

		if name:
			record = self.search([('command', operator, name)] + args, limit=limit)
		else:
			record = self.search(args, limit=limit)

		return record.name_get()