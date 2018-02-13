# ----------------------------------------------------------
# Data Pengadaan (Tender)
# inherit 'mail.thread', 'ir.needaction_mixin'
# order sorting 'tanggal desc'
# ----------------------------------------------------------

from odoo import models, fields, api, exceptions
import datetime

class logistik_tender(models.Model):
	_name = 'logistik.tender'
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_description = "Logistik Tender"
	_rec_name = "nomor"
	_order = "tanggal desc"

	nomor = fields.Char(string='Nomor Tender', size=20, required=True, states={'sp': [('readonly', True)]})
	tanggal = fields.Date(string='Tanggal Tender', required=True, default=fields.Date.today, states={'sp': [('readonly', True)]})
	spm_id = fields.Many2one('logistik.spm', string='Nomor SPM', readonly=True)
	tanggal_spm = fields.Date(related='spm_id.tanggal', string='Tanggal SPM', store=True, readonly=True)
	max_penawaran = fields.Date(string='Tgl Penyerahan Penawaran', states={'sp': [('readonly', True)]})
	tgl_serah = fields.Date(string='Tgl Penyerahan Barang', states={'sp': [('readonly', True)]})
	company_id = fields.Many2one('res.company', string='Perusahaan', default=lambda self: self.env['res.company']._company_default_get(self._name))
	delivery_to = fields.Many2one('res.partner', required=True, string="Tempat Penyerahan", domain=[('is_operating_unit', '=', True)], states={'sp': [('readonly', True)]})
	line_ids = fields.One2many('logistik.tender.lines', 'tender_id', string='Barang yang ditenderkan', required=True)
	spp_ids = fields.One2many('logistik.spp', 'tender_id', string='Penawaran Rekanan', states={'sp': [('readonly', True)]})
	order_ids = fields.One2many('purchase.order', 'tender_id', string='Detail SP', states={'sp': [('readonly', True)]})
	retender_to = fields.Many2one('logistik.tender', string='Nomor Tender Ulang', readonly=True)
	retender_from = fields.Many2one('logistik.tender', string='Tender Ulang Dari', readonly=True)
	state = fields.Selection([
		('draft','Konsep'),
		('spp','SPPH'),
		('wait','Tunggu Persetujuan'),
		('approved','Di-Setujui'),
		('sp','Sudah SP'),
		('cancel','Di-Batalkan'),
	], string='Status', readonly=True,  track_visibility='onchange', default='draft')
	alasan_batal = fields.Text(string='Alasan Pembatalan', readonly=True)
	cancel_by = fields.Many2one('res.users', string='Dibatalkan Oleh', readonly=True)
	cancel_date = fields.Date(string='Tanggal Dibatalkan', readonly=True)
	note = fields.Text(string='Catatan')

	"""
	Constraint field 'nomor' unique
	"""
	_sql_constraints = [
		('nomor_tender_unique', 'unique(nomor, company_id)', 'Nomor Tender tidak boleh dobel!')
	]

	@api.onchange('tgl_serah')
	def onchange_delivery_date(self):
		self.spp_ids.write({'delivery_date':self.tgl_serah})
	
	@api.one
	def action_draft(self):
		"""
		Set 'state' = 'draft' & update record
		"""
		return self.write({'state':'draft'})

	@api.onchange('tanggal')
	def onchange_tanggal(self):
		"""
		Set 'max_penawaran', onchange 'tanggal'
		"""
		self.max_penawaran = datetime.datetime.strptime(self.tanggal, "%Y-%m-%d") + datetime.timedelta(days=3)

	@api.one
	def action_retender(self):
		"""
		Untuk tender ulang
		"""
		if self.retender_to:
			raise exceptions.Warning('Tender ini sudah pernah ditender ulang!')
			return

		# cek dulu apakah sudah ada yg digolongkan
		for spm_line in self.spm_id.line_ids:
			if spm_line.product_id.id in prod_ids and spm_line.golongan != 'none':
				raise exceptions.Warning('SPM Tersebut Sudah di-golongkan!')
				return

		for spm_line in self.spm_id.line_ids:
			if spm_line.product_id.id in prod_ids and spm_line.golongan == 'none':
				spm_line.write({'state':'tender', 'golongan':'tender'})

		lines = []
		prod_ids = []
		for line in self.line_ids:
			prod_ids.append(line.product_id.id)
			lines.append([0, 0, {
				'product_id':line.product_id.id, 
				'unit_id':line.unit_id.id, 
				'kuantum':line.kuantum,
				'pkrat_id':line.pkrat_id.id,
				'tgl_minta':line.tgl_minta,
			}])

		default = {
			'order_ids': None,
			'line_ids': lines,
			'spp_ids': None,
			'nomor': self.spm_id.no_spm,
			'tanggal': datetime.date.today().strftime('%Y-%m-%d'),
			'cancel_by': False,
			'cancel_date': None,
			'alasan_batal': None,
			'tgl_serah': None,
			'state': 'draft',
			'note':None,
		}
				
		retender_to = self.copy(default)
		self.write({'retender_to': retender_to})
		return {
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'logistik.tender',
			'type': 'ir.actions.act_window',
			'target': 'current',
			'context': self._context,
			'res_id':retender_to,
		}
	
	@api.one
	def create_spp(self, partner_id):
		"""
		Create SPP From Tender(Wizard Add Penawaran)
		"""
		lines = []
		for line in self.line_ids:
			lines.append([0, 0, {
				'product_id':line.product_id.id, 
				'unit_id':line.unit_id.id, 
				'kuantum':line.kuantum,
				'kuantum_sp':line.kuantum,
				'spm_line_id': line.spm_line_id.id,
				'tender_line_id':line.id,
				'penyerahan':self.tgl_serah,
			}])
		
		vals = {
			'tender_id':self.id,
			'tgl_serah':self.max_penawaran,
			'spm_id': self.spm_id.id,
			'no_spp': self.nomor,
			'partner_id': partner_id,
			'delivery_to': self.delivery_to.id,
			'golongan':'tender',
			'line_ids': lines,
		}

		return self.env['logistik.spp'].create(vals)

	@api.multi
	def unlink(self):
		"""
		Cek state dulu sebelum didelete
		"""
		for s in self:
			if s.state != 'draft':
				raise exceptions.Warning('Selain Konsep Tender tidak dapat dihapus!')
				return

		for s in self:
			if s.state == 'draft' and s.spm_id:
				for spm_line in s.spm_id.line_ids:
					spm_line.write({'state': 'approved', 'golongan': 'none'})
		return super(logistik_tender, self).unlink()	

	@api.multi
	def action_print_spp(self):
		"""
		Set 'state' = 'spp', update record
		Print report spp
		"""
		if self._check_spp(self.spp_ids):
			for spp in self.spp_ids:
				spp.action_sent()
				
			self.write({'state': 'spp'})
			spp_sorted = self.spp_ids.sorted(key=lambda spp: spp.partner_id.code)
			return self.env['report'].get_action(spp_sorted, 'ka_logistik_pengadaan.report_spp')

	@api.multi
	def action_print_spp_rekap(self):
		"""
		Print report spp rekap
		"""
		if self._check_spp(self.spp_ids):
			return self.env['report'].get_action(self, 'ka_logistik_pengadaan.report_tender_spp')

	@api.one
	def action_approved(self):
		"""
		Set all line_ids 'menang': 1 & update records
		Set approve tender 'state' = 'approved' & update record
		"""
		win_ids = []
		winner_check = []
		for line in self.line_ids:
			winner_check = [spp_line.id for spp_line in line.spp_line_ids if spp_line.menang]
			if not winner_check:
				lower_price = 0
				winner = 0
				for spp_line in line.spp_line_ids:
					if spp_line.harga > 0: 
						if lower_price == 0:
							lower_price = spp_line.harga
							winner = spp_line.id
						else:
							if  spp_line.harga < lower_price: 
								lower_price = spp_line.harga
								winner = spp_line.id
				if winner:
					win_ids.append(winner)

		if win_ids:
			line_ids = self.env['logistik.tender.lines'].browse(win_ids)
			for line in line_ids:
				line.write({'menang': 1})

		if win_ids or winner_check:
			res = self.write({'state':'approved'})
		return
		
	# def action_approved_xxxxx(self, cr, uid, ids, context=None):
	# 	res = {}
	# 	spp_ids = []
	# 	win_ids = []
	# 	for tender in self.browse(cr, uid, ids, context):
	# 		for spp in tender.spp_ids:
	# 			spp_ids.append(spp.id)
			
	# 		for line in tender.line_ids:
	# 			lower_price = 0
	# 			winner = 0
	# 			for spp_line in line.spp_line_ids:
	# 				if lower_price == 0:
	# 					lower_price = spp_line.harga
	# 					winner = spp_line.id
	# 				else:
	# 					if  spp_line.harga < lower_price: 
	# 						lower_price = spp_line.harga
	# 						winner = spp_line.id

	# 			win_ids.append(winner)

	# 	if spp_ids:
	# 		res = self.pool.get('logistik.spp.lines').write(cr, uid, win_ids, {'menang':1}, context)
	# 		res = self.pool.get('logistik.spp').action_confirm(cr, uid, spp_ids, context)
	# 		res = self.write(cr, uid, ids, {'state':'approved'}, context)
	# 	return res

	@api.one
	def action_cancel(self, data):
		"""
		Set logistik.spp in spp_ids 'state': 'cancel'
		Set logistik.spm.lines 'state': 'approved, 'golongan': 'none'
		Set logistik.tender 'state': 'cancel'
		update all record
		"""
		for spp in self.spp_ids:
			spp.write({'state': 'cancel'})
			
			
		tender_prod_ids = []
		for line in self.line_ids:
			tender_prod_ids.append(line.product_id.id)

		for spm_line in self.spm_id.line_ids:
			if spm_line.product_id.id in tender_prod_ids:
				spm_line.write({'state':'approved', 'golongan':'none'})
			
		vals = {
			'nomor': self.nomor + '/B',
			'alasan_batal': data.cancel_reason,
			'cancel_by': data.cancel_by.id,
			'cancel_date': data.cancel_date,
			'state': 'cancel'
		}

		return self.write(vals)
		
	#Tender DIsetui dan dibuat kan konsep SP
	@api.one
	def _get_picking_in(self, company_id):
		type_obj = self.env['stock.picking.type']
		picking_type_ids = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
		if not picking_type_ids:
			picking_type_ids = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
			if not picking_type_ids:
				raise exceptions.Warning("Make sure you have at least an incoming picking type defined!")
		return type_obj.browse(picking_type_ids)
	
	@api.multi
	def action_create_draft_po(self):
		'''
		Membuat Konsep SP dari tender
		Call From	: view_logistik_tender_form<button>
		Return		: list of new created record id and re-direct to open windows Konsep SP
		'''
		self.write({'state':'sp'})
		return self.spp_ids.create_draft_po()
	
	@api.multi
	def action_print_rangking(self):
		"""
		Set 'state': 'wait'
		Print ranking
		"""
		rec_ids = [spp.id for spp in self.spp_ids if spp.state != 'norespon']
		spp_ids = [spp.id for spp in self.spp_ids if spp.total > 0]
		winner_qty = sum(line.winner_qty for line in self.line_ids)
		
		if len(spp_ids) < len(rec_ids):
			raise exceptions.Warning('Ada Harga Rekanan yang belum diterima / dientry.\nMasukkan harga terlebih dahulu dengan memilih Klik PESERTA TENDER kemudian Klik SPPH')
			return
		if winner_qty == 0.00:
			raise exceptions.Warning('Belum ada pemenang. Piling pemenang terlebi dauhulu')
			return
		self.write({'state':'wait'})		
		return self.action_print_tender_result()

	@api.multi
	def action_print_tender_result(self):
		"""
		print report tender result
		"""
		self.ensure_one()
		nomor = self.nomor
		res = self.env['report'].get_action(self, 'ka_logistik_pengadaan.report_tender_result')
		res['name'] = 'TENDER_' + nomor.replace('.', '')
		print res
		return res

	@api.multi
	def action_print_result_sementara(self):
		"""
		call self.action_print_tender_result()
		"""
		if self._check_spp(self.spp_ids):
			return self.action_print_tender_result()

	def _check_spp(self, spp):
		"""
		Check spp before next action
		"""
		if not spp:
			raise exceptions.Warning('Peserta Tender masih kosong')
			return False

		if len(spp) < 3:
			raise exceptions.Warning('Minimal ada Tiga Peserta Tender')
			return False

		return True