from odoo import models, fields, api
import datetime
import time

class TanamanCredit(models.Model):
	_name = 'ka_plantation.credit.farmer'
	_inherit = ['mail.thread', 'ir.needaction_mixin']

	pimpinan_pg = fields.Many2one('hr.employee')
	name = fields.Char(string="Nomor Kredit",size=32)
	farmer_id = fields.Many2one('ka_plantation.farmer', string="Kelompok Tani")
	street = fields.Char(related='farmer_id.street', string="Alamat",readonly=True)
	street2 = fields.Char(related='farmer_id.street2',readonly=True)
	city = fields.Char(related='farmer_id.city',string="Kota",readonly=True)
	no_ktp = fields.Char(related='farmer_id.no_ktp',readonly=True)
	desa_id = fields.Many2one(related='farmer_id.desa_id',readonly=True)
	kecamatan_id = fields.Many2one(related='farmer_id.kecamatan_id',readonly=True)
	kabupaten_id = fields.Many2one(related='farmer_id.kabupaten_id',readonly=True)
	luas = fields.Float(string="Luas Pengajuan", compute='',digits=(6,3))
	harga_ngp = fields.Float(string="Harga Per Ku")
	tanggal = fields.Date(string="Tanggal",default=lambda self: fields.datetime.now())
	luas_petak = fields.Float(string='Luas Kebun',digits=(6,3))
	taks_produksi = fields.Float(string='Potensi Produksi (Ku)')
	total_credit = fields.Float(string="Total Kredit", compute='_compute_total_credit')
	bunga = fields.Float(string="Bunga Pinjaman")
	category_id = fields.Many2one('ka_plantation.credit.category',string="Jenis Kredit")
	register_id = fields.Many2one('ka_plantation.register', string="Register")
	mtt_id = fields.Many2one('ka_plantation.mtt',string="MTT")
	session = fields.Many2one(related='mtt_id.session_id', string="Masa Giling",readonly=True)
	credit_kud_id = fields.Many2one('ka_plantation.credit.kud', string='No.Kredit')
	state =  fields.Selection([
		('draft', "Draft"),
		('validate', "Validate"),
		('approve', "Approve"),
		('paid', "Paid"),
	],default='draft')
	company_id = fields.Many2one('res.company', string='Company', required=True,default=lambda self: self.env['res.company']._company_default_get('ka_plantation.credit.farmer'))
	count_petak = fields.Integer(string="Jumlah Petak",compute="_compute_count_petak")
	voucher_id = fields.Many2one('ka_account.voucher',string="Bukti Kas",readonly=True)
	date_paid = fields.Date(string="Tanggal Bayar",store=True)
	# @api.multi
	# @api.depends('register_ids')
	# def _compute_taks(self):
	# 	for s in self:
	# 		taks = sum([register.taks_produksi for register in s.register_ids])
	# 		luas = sum([register.luas for register in s.register_ids])
	# 		s.taks_produksi = taks
	# 		s.luas_petak = luas

	@api.multi
	@api.depends('register_id')
	def _compute_count_petak(self):
		self.count_petak = len(self.register_id.register_line_ids)

	@api.multi
	@api.depends('harga_ngp','taks_produksi','bunga')	
	def _compute_total_credit(self):
		for s in self:
			total_belum_bunga = s.taks_produksi * s.harga_ngp
			besar_bunga = total_belum_bunga * (s.bunga / 100)
			s.total_credit = total_belum_bunga - besar_bunga

	@api.onchange('register_id')
	def _onchange_register_id(self):
		self.luas_petak = self.register_id.luas
		# self.taks_produksi = self.register_id.taks_produksi

	@api.multi
	def action_draft(self):
		self.state = 'draft'

	@api.multi
	def action_validate(self):
		self.state = 'validate'

	@api.multi
	def action_approve(self):
		self.state = 'approve'

		line_items = []
		data_entry = {}
		journal_id = False
		date_now = datetime.datetime.now().date()
		partner_payment = False
		type_payment = False
		partner = False
		categ_name = self.category_id.name or ''
		regis_name = self.register_id.no_register or ''
		name = categ_name +','+ regis_name
		vals = {
			'account_id' : self.category_id.property_account_id.id,
			'name': name,
			'amount': self.total_credit
		}
		line_items.append((0, 0, vals))
		data_entry = {
				'journal_id' : journal_id,
				'description': self.category_id.name,
				'partner_id': self.farmer_id.partner_id.id,
				'partner_name': self.farmer_id.name,
				# 'partner_bank_id': bank.id,
				# 'partner_bank_acc': bank.acc_number,
				'date' : date_now,
				'printed' : False,
				'state' : 'draft',
				'voucher_lines' : line_items,
				'type' : type_payment
			}
	
		account_voucher_create = self.env['ka_account.voucher'].create(data_entry)
		self.voucher_id = account_voucher_create.id
		return {
				'name': 'Journal Voucher',
				'res_model': 'ka_account.voucher',
				'type': 'ir.actions.act_window',
				'view_mode': 'form',
				'view_type': 'form',
				'res_id': account_voucher_create.id,
				'target': 'current'
			}

	@api.multi
	def action_paid(self):
		self.state = 'paid'

	def open_list_jaminan(self):
		action = self.env.ref('ka_tanaman.action_show_credit_jaminan')
		result = action.read()[0]
		return result

	def open_list_petak(self):
		action = self.env.ref('ka_tanaman.action_show_credit_petak')
		result = action.read()[0]
		temp_ids = [id_petak.area_id.id for id_petak in self.register_id.register_line_ids]
		print temp_ids
		result['domain'] = [('id', 'in', temp_ids)]
		return result

	# @api.multi
	# @api.onchange('date_paid')
	# def _onchange_state(self):
	# 	print "TEST onchange EVENT ______________++++!@$+!@+$+!@+$!@+$+@!$+@!+$!@++$@+"
	# 	if self.date_paid:
	# 		self.state = 'paid'

	# @api.depends('voucher_id.state')
	# def _compute_date_paid(self):
	# 	self.date_paid = self.voucher_id.account_move_id.date
	# 	if self.date_paid:
	# 		self.state = 'paid'
	# 		print "POSTED PAID HARUS NYA INI "
	# 	else:
	# 		print "A+SD+ASD+SA+D+SA+DSA+DAS++SDA++++++++++++"

	# @api.depends('date_paid')
	# def _change_state(self):
	# 	print "TEST PERUBAHAN BENTUK BENDA CAIR KE PADAT"
	# 	if self.date_paid:
	# 		self.state = 'paid'
	# 		print "POSTED PAID HARUS NYA INI "
	# 	else:
	# 		print "A+SD+ASD+SA+D+SA+DSA+DAS++SDA++++++++++++"