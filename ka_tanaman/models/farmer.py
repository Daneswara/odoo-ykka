from odoo import models, fields, api

class Farmer(models.Model):
	_name = 'ka_plantation.farmer'
	_inherits = {'res.partner': 'partner_id'}
	_description = "Kelompok Tani"

	#_ids =  fields.One2many('ka_plantation.register','', string="Area")
	# code = fields.Char(size=10, string="Kode", required=True, ondelete='cascade')
	partner_id = fields.Many2one('res.partner', ondelete='cascade', required=True)
	# kud_id = fields.Many2one('ka_plantation.kud', string="KUD")
	# luas_petak = fields.Float( string="Luas Seluruh Petak", compute='',digits=(5,3))
	desa_id = fields.Many2one('res.desa.kelurahan', string="Desa / Kelurahan", store=True)
	kecamatan_id = fields.Many2one(related='desa_id.kecamatan_id', string="Kecamatan", readonly=True, store=True)
	kabupaten_id = fields.Many2one(related='kecamatan_id.kab_kota_id', string="Kabupaten", readonly=True, store=True)
	pekerjaan = fields.Char(string="Pekerjaan Petani")
	no_ktp = fields.Char(string="No KTP",size=32)
	# credit_ids = fields.One2many('ka_plantation.credit.farmer', 'farmer_id',string="Riwayat Kredit")
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
	bank_account_count = fields.Integer(compute='_compute_bank_count_farmer', string="Bank")
	register_ids = fields.One2many('ka_plantation.register', 'farmer_id', string="Data Register")
	register_count = fields.Integer(compute='_compute_register')

	@api.multi
	def _compute_bank_count_farmer(self):
		bank_data = self.env['res.partner.bank'].read_group([('partner_id', 'in', self.ids)], ['partner_id'], ['partner_id'])
		mapped_data = dict([(bank['partner_id'][0], bank['partner_id_count']) for bank in bank_data])
		for partner in self:
			partner.bank_account_count = mapped_data.get(partner.id, 0)

	@api.multi
	def name_get(self):
		res = []
		for s in self:
			code = s.code or ''
			name = s.name or ''
			res.append((s.id, code + ' - ' + name))
		return res

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

	# override
	@api.multi
	def unlink(self):
		for s in self:
			s.partner_id.unlink()

	def open_register_readonly(self):
		registers = [reg.id for reg in self.register_ids]
		action = self.env.ref('ka_tanaman.action_register_readonly')
		result = action.read()[0]
		result['domain'] = [('id', 'in', registers)]
		return result

	@api.depends('register_ids')
	def _compute_register(self):
		self.register_count = len(self.register_ids)
