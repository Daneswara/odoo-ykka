# ----------------------------------------------------------
# Data SPP (Surat Permintaan Pesanan)
# inherit 'mail.thread, ir.needaction_mixin'
# order sorting 'tanggal desc'
# ----------------------------------------------------------

from odoo import models, fields, api, exceptions
import datetime

class logistik_spp(models.Model):
	_name = 'logistik.spp'
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_description = "LOG1G1 - Header SPP"
	_rec_name = "no_spp"
	_order = "tanggal desc"

	no_spp = fields.Char(string='Nomor SPPH', size=20, states={'confirm': [('readonly', True)], 'order': [('readonly', True)]})
	tanggal = fields.Date(string='Tanggal SPPH', required=True, default=fields.Date.today, states={'confirm': [('readonly', True)], 'order': [('readonly', True)]})
	tgl_serah = fields.Date(string='Tgl Serah', help="Tanggal Penyerahan Penawaran", states={'confirm': [('readonly', True)], 'order': [('readonly', True)]})
	jam_serah = fields.Float(string='Jam Serah', digits=(5, 2), help="Jam Penyerahan Penawaran", states={'confirm': [('readonly', True)], 'order': [('readonly', True)]})
	company_id = fields.Many2one('res.company', string='Perusahaan', default=lambda self: self.env['res.company']._company_default_get(self._name))
	delivery_to = fields.Many2one('res.partner', required=True, string="Tempat Penyerahan", domain=[('is_operating_unit', '=', True)]) 
	delivery_date = fields.Date(compute='_compute_delivery_date', string='Tgl. Penyerahan', store=True)
	tender_id = fields.Many2one('logistik.tender', string='No Tender', states={'confirm': [('readonly', True)], 'order': [('readonly', True)]})
	spm_id = fields.Many2one('logistik.spm', string='Nomor SPM', readonly=True)
	tanggal_spm = fields.Date(related='spm_id.tanggal', type='date', string='Tanggal SPM', store=True, readonly=True)
	partner_id = fields.Many2one('res.partner', string='Rekanan', required=True, states={'confirm': [('readonly', True)], 'order': [('readonly', True)]})
	no_penawaran = fields.Char(string='No. Penawaran', size=30)
	tgl_penawaran = fields.Date(string='Tanggal Penawaran', states={'confirm': [('readonly', True)], 'order': [('readonly', True)]})
	line_ids = fields.One2many('logistik.spp.lines', 'spp_id', string='Detail SPP')
	total = fields.Float(compute='_compute_total', string='Total Harga', digits=(16, 2), store=True)
	total_spph = fields.Float(compute='_compute_total_spph', string='Total SPPH', digits=(16, 2), store=True)
	catatan = fields.Text(string='Catatan')
	golongan = fields.Selection([
		('agen','Agen'),
		('repeat','Repeat'),
		('tender','Tender'),
		('import','import'),
	], string='Golongan', readonly=True)
	state = fields.Selection([
		('draft','Konsep'),
		('sent','Sudah Cetak'),
		('norespon','Tidak Merespon'),
		('confirm','Harga Diterima'),
		('order','Sudah SP'),
		('cancel','Batal'),
	], string='Status', readonly=True, track_visibility='onchange', default='draft')
	tender_state = fields.Selection(related='tender_id.state', selection=[
		('draft','Konsep'),
		('spp','SPPH'),
		('wait','Tunggu Persetujuan'),
		('approved','Di-Setujui'),
		('sp','Sudah SP'),
		('cancel','Di-Batalkan')
	], string='Status Tender')

	_sql_constraints = [
		('spp_rekanan_unique', 'unique(no_spp, partner_id)', 'Rekanan yang sama, Nomor SPP tidak boleh dobel!')
	]

	@api.multi
	@api.depends('line_ids.penyerahan')
	def _compute_delivery_date(self):
		"""
		Computing 'delivery_date', depends 'line_ids.penyerahan'
		"""
		for s in self:
			s.delivery_date = min(s.line_ids, key=lambda x: x['penyerahan'])['penyerahan']

	@api.depends('line_ids.total_harga')
	def _compute_total(self):
		"""
		Computing 'total', depends 'line_ids.total_harga'
		"""

		for s in self:
			_total = 0
			for line in s.line_ids:
				_total += line.total_harga
			s.total = _total

	def action_dummy(self):
		return
 
	@api.depends('line_ids.total_tawar')
	def _compute_total_spph(self):
		"""
		Computing 'total_spph', depends 'line_ids.total_tawar'
		"""
		for s in self:
			_total = 0
			for line in s.line_ids:
				_total += line.total_tawar
			s.total_spph = _total

	@api.onchange('tanggal')
	def onchange_tanggal(self):
		"""
		Set 'tgl_serah', onchange 'tanggal'
		"""
		self.tgl_serah = datetime.datetime.strptime(tgl_spp, "%Y-%m-%d") + datetime.timedelta(days=3)

	@api.one
	def action_norespon(self):
		"""
		Set 'state' = 'norespon' & update record
		"""
		return self.write({'state': 'norespon'})

	@api.one
	def action_draft(self):
		"""
		Set 'state' = 'draft' & update record
		"""
		return self.write({'state': 'draft'})

	@api.one
	def action_sent(self):
		"""
		Set 'state' = 'sent' & update record
		"""
		return self.write({'state': 'sent'})

	@api.one
	def action_cancel(self):
		"""
		Set 'state' = 'cancel' & set 'no_spp' append '/B'
		update record
		"""
		if self.golongan not in ('agen', 'import', 'repeat'):
			raise exceptions.Warning("Hanya SPPH Agen yang dapat dibatalkan.\nUntuk SPPH Tender pembatalan harus melalui Pembatalan Tender")
			return

		if self.state not in ('draft', 'sent'):
			raise exceptions.Warning('SPPH selain konsep tidak dapat dibatalkan')
			return

		if self.line_ids:
			for line in self.line_ids:
				line.spm_line_id.write({'state': 'approved', 'golongan': 'none'})
		
		vals = {}
		vals['state'] = 'cancel'
		vals['no_spp'] = self.no_spp + '/B'
		return self.write(vals)

	@api.multi
	def action_open_spph_tender(self):
		"""
		Open SPPH Tender
		"""
		mod_obj = self.env['ir.model.data']
		res = mod_obj.get_object_reference('ka_logistik_pengadaan', 'view_logistik_spp_tender_form')
		res_id = res and res[1] or False
		return {
			'name': 'Input Harga Penawaran',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'logistik.spp',
			'type': 'ir.actions.act_window',
			'view_id': [res_id],
			'nodestroy': False,
			'context': self._context, 			
			'target': 'new',
			'flags': {'form': {'action_buttons': False, 'options': {'mode': 'edit'}}},
			'res_id': self.id, # and rec_id[0] or False,
		}

	@api.multi
	def action_open_spph_nego(self):
		"""
		Open SPPH nego
		"""
		mod_obj = self.env['ir.model.data']
		res = mod_obj.get_object_reference('ka_logistik_pengadaan', 'view_logistik_spp_tender_nego_form')
		res_id = res and res[1] or False
		return {
			'name': 'Input Harga Negosiasi',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'logistik.spp',
			'type': 'ir.actions.act_window',
			'view_id': [res_id],
			'nodestroy': False,
			'context': self._context, 
			'target': 'new',
			'flags': {'form': {'action_buttons': False, 'options': {'mode': 'edit'}}},
			'res_id': self.id, # and rec_id[0] or False,
		}
		
	@api.multi
	def action_print_spp(self):
		self.action_sent()
		return self.env['report'].get_action(self, 'ka_logistik_pengadaan.report_spp')
	
	@api.multi
	def action_print_harga(self):
		return self.env['report'].get_action(self, 'ka_logistik_pengadaan.report_spp_result')

	@api.one
	def action_confirm(self):
		"""
		Set 'state' = 'confirm'
		"""
		if not self.no_penawaran:
			raise exceptions.Warning('Nomor Penawaran tidak boleh dikosongkan!')
			return
		if not self.tgl_penawaran:
			raise exceptions.Warning('Tanggal Penawaran tidak boleh dikosongkan!')
			return
		if self.total > 0:
			return self.write({'state':'confirm'})
		else:
			raise exceptions.Warning('Harga penawaran belum Di-Entry')
			return

	def _get_picking_in(self, company_id):
		type_obj = self.env['stock.picking.type']
		picking_type_id = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)], limit=1)
		if not picking_type_id:
			picking_type_id = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)], limit=1)
			if not picking_type_id:
				raise exceptions.Warning("Make sure you have at least an incoming picking type defined!")
				return
		return picking_type_id

	def _open_list_draft_sp(self, order_ids):
		''' 
		Methode ini berfungsi untuk meredirect tampilan ketika SP sudah terbuat
			Call From 	: action_create_draft_po
			Rerturn		: Window Action
			Parameter
			@ ids = record id dari SP yang telah dibuat
		'''
		return {
            'name': 'Konsep SP',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'target': 'current',
			'domain': [('id', 'in', order_ids)],
		}

	@api.multi
	def action_create_draft_po(self):
		if self.golongan not in ('agen', 'import', 'repeat'):
			raise exceptions.Warning('Untuk SPPH Tender Pembuatan SP harus melalui menu TENDER!')
			return
			
		return self.create_draft_po()

	@api.multi
	def create_draft_po(self):
		''' 
		Merealisasikan SPP(Surat Permintaan Hrga) menjadi SP(Surat Pesanan)
			Call From	: view_logistik_spp_form<button> & tender.action_create_draft_po
			Return		: Wndows Action`
			Parameter
			@ ids = record id spp yang akan dobuatkan SPP
		'''
		spm_line_ids = []
		order_ids = []
		# for spp in spps:
		for spp in self:
			lines = []
			#picking_type = self._get_picking_in(self.spm_id.company_id.id)
			supplier = spp.partner_id
			for line in spp.line_ids:
				if line.menang or spp.golongan in ('agen', 'import', 'repeat'):
					spm_line_ids.append(line.spm_line_id.id)
					lines.append([0, 0, {
						'product_id':line.product_id.id, 
						'name':(line.product_id.name or '') + (line.product_id.description or ''),
						'product_uom':line.unit_id.id, 
						'product_qty': line.kuantum_sp,
						'account_analytic_id':line.spm_line_id.pkrat_id.account_analytic_id.id,
						'price_unit':line.harga,
						'date_planned':spp.delivery_date,
						'keterangan': '%s %s' % (line.spm_line_id.catatan or '', line.keterangan or ''),
						'spm_line_id': line.spm_line_id.id,
					}])

			# sp = False
			if lines:
				ttd_dir = spp.company_id.dept_dirut.manager_id.id
				ttd_keu = spp.company_id.dept_dirkeu.manager_id.id 
				ttd_log = spp.company_id.dept_log.manager_id.id 
				order_no = spp.env['ir.sequence'].next_by_code('purchase.order')				
				vals = {
					'name': spp.spm_id.no_spm + "/" + order_no[len(order_no)-3:len(order_no)],
					'spp_id': spp.id,
					'tender_id':spp.tender_id.id,
					'partner_ref':spp.no_penawaran,
					'spm_id': spp.spm_id.id,
					'partner_id': spp.partner_id.id,
					'operating_unit_id': spp.delivery_to.id,
					#'picking_type_id': picking_type.id,
					'golongan': spp.golongan,
					'ttd_dir': ttd_dir,
					'ttd_keu': ttd_keu,
					'ttd_log': ttd_log,
					'order_line': lines,
					'date_planned': spp.tender_id.tgl_serah if spp.golongan == 'tender' else spp.delivery_date,
				}
				order = self.env['purchase.order'].create(vals)
				order_ids.append(order.id)
				spp.write({'state':'order'})
				if order:
					spm_lines = self.env['logistik.spm.lines'].browse(spm_line_ids)
					for spm_line in spm_lines:
						spm_line.write({'golongan' : spp.golongan, 'state': 'draftsp', 'order_id': order.id})
			
			# print sp
		return self._open_list_draft_sp(order_ids)