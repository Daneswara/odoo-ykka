from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Register(models.Model):
	_name = 'ka_plantation.register'
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_rec_name = 'no_register'

	name = fields.Char(string="Atas Nama", size=64)
	no_register = fields.Char(string="No. Register", size=6, required=True)
	farmer_id = fields.Many2one('ka_plantation.farmer', required=True, string="No. Induk Petani")
	mtt_id = fields.Many2one('ka_plantation.mtt', string='MTT')
	session_id = fields.Many2one(related='mtt_id.session_id', string="Masa Giling", readonly=True, store=True)
	luas = fields.Float(compute='_compute_produksi', store=True)
	# company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
	register_type = fields.Selection([
		('ts', "TS"),
		('trk', "TRK"),
		('trm', "TRM"),
	],string="Type", default='trm')
	# desa_id = fields.Many2one('res.desa.kelurahan', string="Desa")
	# kecamatan_id = fields.Many2one('res.kecamatan', string="Kecamatan")
	# kabupaten_id = fields.Many2one('res.kab.kota', string="Kabupaten")
	area_sampling_id = fields.Many2one('ka_plantation.sampling.area')
	mandor_id = fields.Many2one('hr.employee', string='Mandor')
	plpg_id = fields.Many2one('hr.employee', string='PLPG')
	manager_id = fields.Many2one('hr.employee', string='Kasubsie')
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id,readonly=True)
	taks_produksi = fields.Float(compute='_compute_produksi', string="Taksasi Produksi", store=True)
	# taks_maret = fields.Float(string="Taks. Maret (Ku)", compute="_compute_produksi", store=True)
	# taks_des = fields.Float(string="Taks. Desember (Ku)", compute="_compute_produksi", store=True)
	sisa_ku = fields.Float(compute='_compute_produksi', string="Sisa", store=True)
	tergiling_ku = fields.Float(compute='_compute_produksi', string="Tergiling", store=True)
	kud_id = fields.Many2one('ka_plantation.kud',string="Anggota KUD")
	register_line_ids = fields.One2many('ka_plantation.register.line', 'register_id', string="Detail Register")
	contract_id = fields.Many2one('ka_plantation.ts.contract', string="No. Proposal")
	credit_id = fields.Many2one('ka_plantation.credit.farmer', string="No. Kredit")
	state = fields.Selection([("draft", "Draft"),
							("propose", "Propose"),
							("approve", "Validate")],
                             string = "State", default="draft", track_visibility='onchange')
	is_rekanan = fields.Boolean(string="Rekanan ",default=False)

	_sql_constraints = [
		('register_unique', 'UNIQUE(no_register,mtt_id)', 'Nomor Register sudah terdaftar atas nama Petani lain!')
	]			

	# @api.multi
	# @api.onchange('taks_produksi','tergiling_ku')
	# def _compute_sisa(self):
	# 	self.sisa_ku = self.taks_produksi - self.tergiling_ku

	@api.multi
	@api.depends('register_line_ids.taks_produksi')
	def _compute_produksi(self):
		for s in self:
			s.taks_produksi = sum([line.taks_produksi for line in s.register_line_ids])
			s.sisa_ku = sum([line.sisa_ku for line in s.register_line_ids])
			s.tergiling_ku = sum([line.tergiling_ku for line in s.register_line_ids])
			s.luas = sum([line.luas for line in s.register_line_ids])
			# s.taks_maret = sum([line.taks_maret for line in s.register_line_ids])
			# s.taks_des = sum([line.taks_des for line in s.register_line_ids])

	@api.one
	def action_propose(self):
		self.state = 'propose'
		
	@api.one
	def action_approve(self):
		for line in self.register_line_ids:
			# self.env['ka_plantation.register.line'].search([('area_id','=',line.area_id.id)])
			vals ={
				'mtt_id'  : line.mtt_id.id,
				'area_id' : line.area_id.id,
				'desa_id' : line.desa_id.id,
				'varietas_id' : line.varietas_id.id,
				'intensifikasi_id' : line.intensifikasi_id.id,
				'tebang_periode_id' : line.tebang_periode_id.id,
				'tanam_periode_id' : line.tanam_periode_id.id,
				'register_type' : line.register_type
			}
			result = self.env['ka_plantation.area.agronomi'].search([('area_id','=',line.area_id.id)])
			print vals
			if result:
				self.env['ka_plantation.area.agronomi'].update(vals)
			else:
				self.env['ka_plantation.area.agronomi'].create(vals)
		self.state = 'approve'

	@api.one
	def action_set_draft(self):
		self.state = 'draft'
        
class RegisterLine(models.Model):
	_name = 'ka_plantation.register.line'

	petani = fields.Char(string="Petani", size=30)
	area_id = fields.Many2one('ka_plantation.area', string="Kode Petak")
	register_id = fields.Many2one('ka_plantation.register', string="No. Register")
	intensifikasi_id = fields.Many2one('ka_plantation.intensifikasi', string="Intensifikasi")
	varietas_id = fields.Many2one('ka_plantation.varietas', string="Varietas")
	tebang_periode_id = fields.Many2one('ka_plantation.periode', string="Masa Tebang")
	tanam_periode_id = fields.Many2one('ka_plantation.periode', string="Masa Tanam")
	luas = fields.Float(related='area_id.luas', digits=(5,3), string="Luas", store=True)
	taks_produksi = fields.Float(string="Taks. Produksi (Ku)")
	produktivitas = fields.Float(string="Produktivitas Petak (Ku/Ha)")
	sisa_ku = fields.Float(string="Sisa Produksi (Ku)")
	tergiling_ku = fields.Float(string="Tergiling (Ku)")
	desa_id = fields.Many2one(related='area_id.desa_id', string="Desa")
	kecamatan_id = fields.Many2one(related='area_id.kecamatan_id', string="Kecamatan",store=True)
	kabupaten_id = fields.Many2one(related='area_id.kabupaten_id', string="Kabupaten")
	farmer_id = fields.Many2one(related='register_id.farmer_id', string="Kelompok Tani")
	mtt_id = fields.Many2one('ka_plantation.mtt',string="MTT",store=True)
	session_id = fields.Many2one(related='register_id.session_id', string="Masa Giling")
	register_type = fields.Selection(related='register_id.register_type', string="Type",store=True)
	employee_id = fields.Many2one(related='register_id.plpg_id', string="PLPG")
	gps_polygon = fields.Text(related='area_id.gps_polygon', string="GPS Polygon")
	is_rekanan = fields.Boolean(related='register_id.is_rekanan',string="Rekanan")
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
	
	# _sql_constraints = [
	# 	('petak_unique', 'UNIQUE(area_id,mtt_id)', 'Nomor Petak sudah terdaftar atas pada Register lain!')
	# ]		

	# @api.one
	# @api.constrains('area_id','mtt_id')
	# def _constraint_area_mtt(self):
	# 	if len(self.search([('area_id', '=', self.area_id.id),('mtt_id','=',self.mtt_id.id)])) > 1:
	# 		raise ValidationError("Nomor Petak sudah terdaftar atas pada Register lain!")

	@api.onchange('tergiling_ku')
	def _onchange_tergiling(self):
		self.sisa_ku = self.taks_produksi - self.tergiling_ku
	
	@api.onchange('area_id')
	def onchange_area_id(self):
		agronomi = self.env['ka_plantation.area.agronomi'].search([('area_id', '=', self.area_id.id),('mtt_id','=',self.mtt_id.id)])
		if agronomi:
			self.varietas_id = agronomi.varietas_id.id
			self.intensifikasi_id = agronomi.intensifikasi_id.id
			self.tanam_periode_id = agronomi.tanam_periode_id.id
			self.tebang_periode_id = agronomi.tebang_periode_id.id


	@api.onchange('area_id','varietas_id','intensifikasi_id')
	def onchange_taksasi(self):
		sampling = self.env['ka_plantation.sampling'].search([('mtt_id','=',self.mtt_id.id),('company_id','=',self.register_id.company_id.id),('taks_periode','=','maret')])
		if sampling:
			for s in sampling:
				for line in s.line_ids:
					for kom in line.kombinasi_ids:
						if kom.varietas_id == self.varietas_id and kom.intensifikasi_id == self.intensifikasi_id and kom.kecamatan_id == self.area_id.kecamatan_id:
							self.taks_produksi = kom.produktivitas
		
	# @api.onchange('area_id')
	# def _onchange_area(self):
	# 	agronomi = self.env['ka_plantation.area.agronomi'].

	# @api.model
	# def create(self, vals):
	# 	print '---------------- create --------------------'
	# 	print self.area_id
	# 	print vals
	# 	return super(RegisterLine, self).create(vals)

	# @api.multi
	# def write(self, vals):
	# 	print '---------------- write ----------------------'
	# 	print self.area_id
	# 	print vals
	# 	return super(RegisterLine, self).write(vals)