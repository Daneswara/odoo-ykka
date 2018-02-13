from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime

class TsContract(models.Model):
	_name = 'ka_plantation.ts.contract'
	_description = 'Pengadaan Kebun TS'
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_inherits = {'account.analytic.account': "account_analytic_id"}

	nomor = fields.Char(string='Nomor Lama', size=5)
	date_contract = fields.Date('Tanggal', default=lambda self: fields.datetime.now())
	pemilik = fields.Char(string='Nama Pemilik', size=32, required=True)
	status_lahan = fields.Selection([('hgu', 'HGU'), ('bengko', 'BENGKOK'), ('shm', 'HAK MILIK'), ('sewa', 'SEWA'),('bondodeso','BONDODESO / KAS DESA')], string='Kepemilikan')
	desa_id = fields.Many2one('res.desa.kelurahan', string='Desa', required=True)
	kecamatan_id = fields.Many2one(related='desa_id.kecamatan_id', string='Kecamatan', readonly=True)
	kabupaten_id = fields.Many2one(related='desa_id.kab_kota_id', string='Kabupaten',  readonly=True)
	luas = fields.Float(compute='_compute_area', string='Luas Lahan',digits=(5,3))
	count_area = fields.Integer(compute='_compute_area', string='Jumlah Petak')
	area_type = fields.Selection([('sawah', 'SAWAH'), ('tegal', 'TEGAL')], string='Kategori Lahan', default='sawah')
	kesuburan = fields.Selection([('kurang', 'KURANG'), ('cukup', 'CUKUP'), ('baik', 'BAIK')], string='Kesuburan', default='cukup')
	pengairan = fields.Char(string="Pengairan", size=16)
	kemiringan = fields.Selection([('miring', 'MIRING'), ('datar', 'DATAR')], string='Kemiringan', default='datar')
	jalan_tebang = fields.Char('Jalan Tebang Angkut', size=16)
	jalan_kampung = fields.Char('Jalan Kampung', size=16)
	rawan_kering = fields.Boolean('Rawan Kering', default=False)
	rawan_banjir = fields.Boolean('Rawan Banjir', default=False)
	patusan = fields.Char('Patusan', size=16)
	eks_tanaman = fields.Char('Tanaman Sebelumnya', size=16)
	taks_produksi = fields.Integer(string='Potensi Produksi (ku/ha)')
	tanggal_buka_lahan = fields.Date('Buka Lahan Bulan')
	tanggal_rencana_tebang = fields.Date('Renc. Tebang Bulan')
	buka_lahan_dengan = fields.Char('Buka Lahan Dengan', size=16, default='TRAKTOR')
	varietas_id = fields.Many2one('ka_plantation.varietas', string="Rencana Varietas")
	tenaga_kerja = fields.Char('Tenaga Kerja Lokal', size=16, default='CUKUP')
	kondisi_sosial = fields.Char('Kondisi Sosial', size=16, default='KONDUSIF')	
	date_start = fields.Date(string="Mulai", required=True)
	date_end = fields.Date(string="Sampai Dengan", required=True)
	contract_duration = fields.Float(compute='_compute_duration', string='Masa Kerja Sama')
	eks_varietas_id = fields.Many2one('ka_plantation.varietas', string="Varietas Sebelumnya")
	eks_produksi = fields.Integer('Produksi Sebelumnya')
	account_analytic_id = fields.Many2one('account.analytic.account', string="Perkiraan Analisis", required=True, ondelete="cascade")
	manager_id = fields.Many2one('hr.employee', string="Kasubsie", required=True,track_visibility='onchange')
	employee_id = fields.Many2one('hr.employee', string="Mandor Kebun", required=True)
	description = fields.Text(string="Catatan")
	area_ids = fields.Many2many('ka_plantation.area', 'ts_contract_area_rel', 'contract_id', 'area_id', string='Data Petak Kebun')
	register_ids = fields.One2many('ka_plantation.register', 'contract_id', string='Register')
	contract_line_ids = fields.One2many('ka_plantation.ts.contract.line', 'contract_id', string='Rencana Biaya')
	state = fields.Selection([("draft", "Draft"),
							("propose", "Propose"),
							("approve", "Open"),
							("close", "Close"),
                            ("cancel", "Cancel")],
                            string = "State", default="draft", track_visibility='onchange')
	# total_produksi = fields.Integer(string="Total Produksi",compute='_compute_total_produksi')
	_sql_constraints = [
		('ts_contract_nomor_unique', 'UNIQUE(nomor)', 'Nomor sudah ada, silahkan masukkan nomor lain!'),
		('ts_contract_no_proposal_unique', 'UNIQUE(code)', 'No. Proposal sudah ada, silahkan masukkan nomor lain!')
	]
	
	@api.depends('date_end', 'date_start')
	def _compute_duration(self):
		for this in self:
			if this.date_end and this.date_start:
				end_date = datetime.strptime(this.date_end, '%Y-%m-%d')
				start_date = datetime.strptime(this.date_start, '%Y-%m-%d')
				rd = relativedelta(end_date, start_date)
				duration = rd.years + (rd.months/12.0)
				this.contract_duration = duration

	@api.depends('area_ids')
	def _compute_area(self):
		for this in self:
			this.luas = sum(area.luas for area in this.area_ids)
			this.count_area = len(this.area_ids)
	
	@api.multi
	def unlink(self):
		analytic_accounts_to_delete = self.env['account.analytic.account']
		for contract in self:
			analytic_accounts_to_delete |= contract.account_analytic_id
		res = super(TsContract, self).unlink()
		analytic_accounts_to_delete.unlink()
		return res

	# @api.depends('luas','taks_produksi')
	# def _compute_total_produksi(self):
	# 	self.total_produksi = self.luas * self.taks_produksi

	# @api.onchange('luas','taks_produksi')
	# def _onchange_luas_taks(self):
	# 	self.total_produksi = self.luas * self.taks_produksi
	# 	for s in self.contract_line_ids:
	# 		if s:
	# 			s.update({'taks_produksi':self.total_produksi})
	# 			# super(TsContract, self).write(s)
	# 			# print s
	# 			return

	@api.one
	def action_propose(self):
		self.state = 'propose'
		
	@api.one
	def action_approve(self):
		self.state = 'approve'

	@api.one
	def action_close(self):
		self.state = 'close'

	@api.one
	def action_cancel(self):
		self.state = 'cancel'

	@api.one
	def action_set_draft(self):
		self.state = 'draft'

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

	@api.multi
	def open_list_petak(self):
		petak_ids = []
		for j in self.area_ids:
			petak_ids.append(j.id)

		action = self.env.ref('ka_tanaman.action_show_petak_ts_contract')
		result = action.read()[0]
		result['domain'] = [('id', 'in', petak_ids)]
		return result

	# @api.onchange('manager_id')
	# def onchange_manager_id(self):
	# 	print "+++++++++++++++++++++++++++++++="
	# 	print self.manager_id.id
	# 	print self.env.user.manager_id.id

	# # @override
	# @api.model
	# def create(self, vals):
		# self._set_area_status(vals['area_id'])
		# return super(TsContract, self).create(vals)

	# # @override
	# @api.multi
	# def write(self, vals):
		# if vals.has_key('area_id'):
			# self.area_id.set_contract(False)
			# self._set_area_status(vals['area_id'])
		# return super(TsContract, self).write(vals)

	# # @override
	# @api.multi
	# def unlink(self):
		# self.area_id.set_contract(False)
		# return super(TsContract, self).unlink()

	# def _set_area_status(self, area_id):
		# area = self.env['ka_plantation.area'].browse(area_id)
		# for a in area:
			# a.set_contract(True)

class TsContractLine(models.Model):
	_name = 'ka_plantation.ts.contract.line'
	_description = 'Rencana Biaya Pengadaan TS'
	
	contract_id = fields.Many2one('ka_plantation.ts.contract', string="No. Proposal")
	mtt_id = fields.Many2one('ka_plantation.mtt', string='MTT')
	intensifikasi_id = fields.Many2one('ka_plantation.intensifikasi', string="Intensifikasi")
	varietas_id = fields.Many2one('ka_plantation.varietas', string="Varietas")
	cost_total = fields.Float(compute='_compute_all', string='Total Biaya', digits=(12,0))
	#taks_produksi = fields.Integer(related='contract_id.taks_produksi', string='Taks. Produksi', store=False)
	# taks_produksi = fields.Integer(string='Taks. Produksi',default=lambda self: self._context.get('default_total_produksi'))
	taks_produksi = fields.Integer(string='Taks. Produksi')
	cost_ku = fields.Float(compute='_compute_all', string='Biaya/KU', digits=(12,0))
	cost_ta = fields.Float(compute='_compute_all', string='Biaya TA', digits=(12,0))
	cost_ku_ta = fields.Float(compute='_compute_all', string='Total Biaya/KU', digits=(12,0))
	cost_line_ids = fields.One2many('ka_plantation.ts.contract.cost.line', 'contract_cost_id', string='Uraian Biaya')
	register_id = fields.Many2one('ka_plantation.register', string="Register")
	# luas = fields.Float(string="Luas",digits=(5,3),compute='_compute_luas_taks',readonly=False)
	# potensi_produksi = fields.Integer(string='Potensi Produksi (ku/ha)',compute='_compute_luas_taks')
	
	
	@api.depends('cost_line_ids.cost_amount')
	def _compute_all(self):
		for this in self:
			taks_produksi = this.taks_produksi
			if taks_produksi == 0:
				break
			# this.taks_produksi = taks_produksi
			this.cost_total = sum(line.cost_amount for line in this.cost_line_ids if not line.is_ta)
			this.cost_ku = this.cost_total / taks_produksi
			this.cost_ta = sum(line.cost_amount for line in this.cost_line_ids if line.is_ta)
			this.cost_ku_ta = this.cost_ku + this.cost_ta

	# @api.one
	# @api.depends('contract_id.luas','contract_id.taks_produksi')
	# def _compute_luas_taks(self):
	# 	print "CEK COMPUTE_______________________----"
	# 	# self.luas = self.contract_id.luas
	# 	# self.potensi_produksi = self.contract_id.taks_produksi
	# 	self.taks_produksi = self.contract_id.luas * self.contract_id.potensi_produksi

	# @api.one
	# @api.depends()
	# def _compute_taks(self):
	# 	print "------ POTENSI PRODUKSI -------"

	# @api.onchange('luas','potensi_produksi')
	# def _onchange_luas_taks(self):
	# 	print "onchange luas taks"
	# 	print self.luas
	# 	print self.potensi_produksi
	# 	self.taks_produksi = self.luas * self.potensi_produksi
				
	@api.onchange('intensifikasi_id')
	def onchange_intesifikasi(self):
		cost_line_ids = None
		new_lines = self.env['ka_plantation.ts.contract.cost.line']
		for cost in self.intensifikasi_id.cost_template_ids:
			data = {
				'cost_template_id':cost.id,
				'is_ta':cost.is_ta
			}
			new_line = new_lines.new(data)
			new_lines += new_line
		self.cost_line_ids += new_lines
		
	def open_create_register(self):
		lines = []
		for area in self.contract_id.area_ids:
			lines.append([0,0, {
				'area_id': area.id,
				'taks_produksi': self.taks_produksi,
				'intensifikasi_id': self.intensifikasi_id.id,
			}])
		mod_obj = self.env['ir.model.data']
		res = mod_obj.get_object_reference('ka_tanaman', 'view_form_register_ts')
		view_id = res and res[1] or False
		return {
			'name': 'Pendaftaran Register TS',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'ka_plantation.register',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'nodestroy': False,
			'view_id': [view_id],
			'context':{
					'default_mtt_id': self.mtt_id.id, 
					'default_register_type': 'ts', 
					'default_name': self.contract_id.name,
					# 'default_employee_id': self.contract_id.employee_id.id,
					'default_manager_id': self.contract_id.manager_id.id,
					'default_contract_id': self.contract_id.id,					
					'default_register_line_ids': lines,
					'contract_line_id':self.id,
			},
			'flags': {'form': {'action_buttons': False, 'options': {'mode': 'edit'}}},
		}
	
	
class TsContractCostLine(models.Model):
	_name = 'ka_plantation.ts.contract.cost.line'
	_description = 'Detail Rencana Biaya Pengadaan TS'
	
	contract_cost_id = fields.Many2one('ka_plantation.ts.contract.line', string='Rincian Biaya', ondelete='cascade')
	cost_template_id = fields.Many2one('ka_plantation.intensifikasi.cost.template', string='Nama Biaya')
	account_id = fields.Many2one('account.account', string='Perkiraan')
	luas = fields.Float(string="Luas",digits=(5,3),related='contract_cost_id.contract_id.luas')
	# luas = fields.Float(string="Luas",digits=(5,3))
	taks_produksi = fields.Integer(string='Potensi Produksi (ku/ha)',related='contract_cost_id.contract_id.taks_produksi')
	harga = fields.Float(string="Harga",digits=(12,0))
	cost_amount = fields.Float('Jumlah', digits=(12,0))
	uom_id = fields.Many2one(string='Satuan', related='cost_template_id.uom_id', readonly=True)
	is_ta = fields.Boolean('Biaya TA')


	@api.onchange('harga')
	def _onchange_cost_amount(self):
		if self.cost_template_id.name == "Biaya T & A":
			self.cost_amount = self.contract_cost_id.taks_produksi * self.harga
		else:
			self.cost_amount = self.luas * self.harga