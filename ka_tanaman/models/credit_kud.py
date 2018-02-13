from odoo import models, fields, api

class CreditKud(models.Model):
	_name = 'ka_plantation.credit.kud'
	_inherit = ['mail.thread', 'ir.needaction_mixin']

	name = fields.Char(string="No Surat",required=True)
	tanggal = fields.Date(string="Tanggal Surat",default=lambda self: fields.datetime.now(),required=True)
	kud_id = fields.Many2one('ka_plantation.kud',string="Nama KUD",required=True)
	# ketua_kud_id = fields.Many2one(related='kud_id.ketua_kud_id',string="Ketua KUD",readonly=True)
	ketua_kud = fields.Char(related='kud_id.ketua_kud',string="Ketua KUD",readonly=True)
	street = fields.Char(related='kud_id.street',readonly=True)
	harga_ngp = fields.Float(string="Harga Per Ku",required=True)
	luas_petak = fields.Float(string="Luas Kebun",digits=(5,3))
	taks_produksi = fields.Float(string="Taks. Produksi")
	total_credit = fields.Float(compute='_compute_total_credit',string="Total kredit")
	bunga = fields.Float(string="Bunga Pinjaman",required=True)
	farmer_credit_ids = fields.One2many('ka_plantation.credit.farmer','credit_kud_id')
	mtt_id = fields.Many2one('ka_plantation.mtt',string="MTT")
	session = fields.Many2one(related='mtt_id.session_id', string="Masa Giling",readonly=True)
	state =  fields.Selection([
		('draft', "Draft"),
		('validate', "Validate"),
		('approve', "Approve"),
		('paid', "Paid"),
	],default='draft')
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
	count_farmer = fields.Integer(compute='_compute_count_farmer')
	register_id = fields.Many2one('ka_plantation.register', string="Register")
	count_petak = fields.Integer(string="Jumlah Petak",compute="_compute_count_petak")

	def _compute_luas(self):
		print self.farmer_id

	@api.multi
	@api.depends('register_id')
	def _compute_count_petak(self):
		self.count_petak = len(self.register_id.register_line_ids)

	@api.onchange('register_id')
	def _onchange_register_id(self):
		self.luas_petak = self.register_id.luas
		self.taks_produksi = self.register_id.taks_produksi

	@api.depends('harga_ngp','taks_produksi','bunga')	
	def _compute_total_credit(self):
		total_belum_bunga = self.taks_produksi * self.harga_ngp
		besar_bunga = total_belum_bunga * (self.bunga / 100)
		self.total_credit = total_belum_bunga - besar_bunga

	@api.multi
	def action_draft(self):
		self.state = 'draft'

	@api.multi
	def action_validate(self):
		self.state = 'validate'

	@api.multi
	def action_approve(self):
		self.state = 'approve'

	@api.multi
	def action_paid(self):
		self.state = 'paid'

	def open_list_jaminan(self):
		action = self.env.ref('ka_tanaman.action_show_credit_jaminan')
		result = action.read()[0]
		return result

	def open_list_farmer(self):
		action = self.env.ref('ka_tanaman.action_show_credit_farmer')
		result = action.read()[0]
		# temp_ids = [cek.credit_kud_id.id for cek in self.farmer_credit_ids]
		result['domain'] = [('credit_kud_id', '=', self.id)]
		result['context'] = {
			'default_session_id':self.session.id,
			'default_tanggal':self.tanggal,
			'default_name':self.name,
			'default_credit_kud_id':self.id
			}
		return result

	@api.multi
	def _compute_count_farmer(self):
		count = 0
		for s in self.farmer_credit_ids:
			if s.credit_kud_id != self.id:
				count = count + 1
		# 		print s.credit_kud_id
		# 		print "++++++++++++++++++"
		# print count
		self.count_farmer = count

	def open_list_petak(self):
		action = self.env.ref('ka_tanaman.action_show_credit_kud_petak')
		result = action.read()[0]
		temp_ids = [id_petak.area_id.id for id_petak in self.register_id.register_line_ids]
		print temp_ids
		result['domain'] = [('id', 'in', temp_ids)]
		return result
	
	# def open_list_petak(self):
	# 	action = self.env.ref('ka_tanaman.action_show_credit_kud_petak')
	# 	result = action.read()[0]
	# 	register_ids = [register.register_ids for register in self.farmer_credit_ids]
	# 	join_register = register_ids[0]+register_ids[1]
	# 	area_ids = [area.area_id.id for area in join_register]
	# 	result['domain'] = [('id', 'in', area_ids)]
	# 	luas = sum([cari.luas for cari in join_register])
	# 	self.luas_petak = luas
	# 	return result