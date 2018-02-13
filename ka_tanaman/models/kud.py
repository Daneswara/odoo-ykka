from odoo import models, fields, api

class Kud(models.Model):
	_name = 'ka_plantation.kud'
	_inherits = {'res.partner': 'partner_id'}

	# ketua_kud_id = fields.Many2one('ka_plantation.farmer',string="Ketua Kelompok")
	partner_id = fields.Many2one('res.partner', ondelete='cascade', required=True)
	ketua_kud = fields.Char(string="Ketua KUD", size=64)
	city = fields.Many2one('res.kab.kota',string="KOTA")
	# farmer_ids = fields.One2many('ka_plantation.farmer', 'kud_id', string="Petani")
	register = fields.Char(size=6,string="Register")
	# property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
	# 	string="Account Payable", oldname="property_account_payable",
	# 	domain="[('internal_type', 'in', ['payable', 'receivable']), ('deprecated', '=', False)]",
	# 	help="This account will be used instead of the default one as the payable account for the current partner",
	# 	required=True)

	# property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
	# 	string="Account Receivable", oldname="property_account_receivable",
	# 	domain="[('internal_type', 'in', ['payable', 'receivable']), ('deprecated', '=', False)]",
	# 	help="This account will be used instead of the default one as the receivable account for the current partner",
	# 	required=True)

	# @override
	@api.multi
	def name_get(self):
		res = []
		for s in self:
			register = s.register or ''
			name = s.name or ''
			res.append((s.id, register + ' - ' + name))

		return res

	# @override
	@api.model
	def name_search(self, name='', args=None, operator='ilike', limit=80):
		if not args:
			args = []

		if name:
			record = self.search([('register', operator, name)] + args, limit=limit)
			if not record:
				record = self.search([('name', operator, name)] + args, limit=limit)
		else:
			record = self.search(args, limit=limit)

		return record.name_get()

	# override
	@api.multi
	def unlink(self):
		for s in self:
			s.partner_id.unlink()