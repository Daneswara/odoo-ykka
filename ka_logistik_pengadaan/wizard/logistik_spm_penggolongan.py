from odoo import models, fields, api, exceptions
from datetime import date

class logistik_spm_penggolongan(models.TransientModel):
	_name = 'logistik.spm.penggolongan'
	_description = "Wizard Penggolongan SPM"

	spm_id = fields.Many2one('logistik.spm', string='Nomor SPM')
	line_ids = fields.One2many('logistik.spm.penggolongan.lines', 'golongan_id', string='Detail SPM')
	partner_id = fields.Many2one('res.partner', string='Rekanan')
	order_id = fields.Many2one('purchase.order', string='Nomor SP')
	company_id = fields.Many2one('res.company', string='Perusahaan', default=lambda self: self.env['res.company']._company_default_get(self._name))
	pengadaan = fields.Selection([
		('RD', 'Direksi'),
		('RP', 'Lokal')
	], string='Jenis SP')
	golongan = fields.Selection([
		('none','Belum digolongkan'),
		('import','Import'),
		('agen','Agen'),
		('repeat','Repeat'),
		('tender','Tender'),
	], string='Penggolongan', default='none')
	state = fields.Selection([
		('choose','Choose'),
		('set','Set'),
	], string='Status', default='choose', readonly=True)

	@api.model
	def default_get(self, fields_list):
		res = super(logistik_spm_penggolongan, self).default_get(fields_list)
		line_ids = self._context.get('active_ids', [])
		spm_lines = self.env['logistik.spm.lines'].browse(line_ids)
		lines = []
		spm_ids = []
		pengajuan_ids = []
		dept_ids = []
		for spm_line in spm_lines:
# 			if not spm_line.product_id:
# 				raise exceptions.Warning('Untuk barang : [ %s ] Kode barang belum didefiniskan!' % spm_line.name_spec)
# 				return
			if spm_line.state <> 'approved':
				raise exceptions.Warning('Permintaan yang belum di-Setujui tidak dapat diproses')
				return

			line = {
				'spm_line_id' : spm_line.id,
				'spm_id' : spm_line.spm_id.id,
				'product_id' : spm_line.product_id.id,
				'product_description': spm_line.spesifikasi,
				'unit_id' : spm_line.unit_id.id,
				'kuantum' : spm_line.kuantum_sp if self._context.get('pengadaan') == 'RD' else spm_line.kuantum_spm,
				'tgl_minta' : spm_line.tgl_minta,
				'pkrat_id' : spm_line.pkrat_id.id,
			}
			spm_ids.append(['spm_id',spm_line.spm_id.id])
			dept_ids.append(['dept_id',spm_line.department_id.id])
			pengajuan_ids.append(['spm_id',spm_line.pengajuan_id.id])
			lines.append([0, 0, line])
			
		num_spm = set(map(lambda x:x[1], spm_ids))
		num_dept = set(map(lambda x:x[1], dept_ids))
		if len(num_spm) > 1:
			raise exceptions.Warning('Penggolongan hanya berlaku untuk satu Nomor SPM!')
			return

		if self._context.get('pengadaan') == 'RP' and len(num_dept) > 1:
			raise exceptions.Warning('Realisasi SPM menjadi PO hanya berlaku untuk satu Department!')
			return
        
		spm_id = spm_lines[0].spm_id.id	
		spm = self.env['logistik.spm'].browse(spm_id)
		gol = 'none'
		pengadaan = self._context.get('pengadaan')
		if pengadaan == 'RP':
			gol = 'agen'

		res.update(
			spm_id = spm_id,
			pengadaan = pengadaan,
			golongan = gol,
			line_ids = lines
		)
		return res

	@api.multi
	def action_open_form_repeat(self):
		mod_obj = self.env['ir.model.data']
		self.write({'state': 'set'})
		res = mod_obj.get_object_reference('ka_logistik_pengadaan', 'view_repeat_form')
		view_id = res and res[1] or False
		return {
			'name': 'Repeat Order',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'logistik.spm.penggolongan',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'view_id': [view_id],
			'res_id': self.id, 
			'context': self._context,
		}
		
	def check_empty_uom_lines(self):
		res = False
		for line in self.line_ids:
			if line.product_id:
				if not line.unit_id:
					res = True
					break
		return res

	@api.multi
	def action_golongan(self):
		self.ensure_one()
		if self.check_empty_uom_lines():
			raise exceptions.UserError("Field 'Satuan' tidak boleh kosong.")
		spm_lines = self.env['logistik.spm.lines']
		spm_ids = self._context.get('active_ids', [])
		mod_obj = self.env['ir.model.data']
		ret_from = {}
		
		#jika SPM di golongkan sebagai AGEN
		if self.golongan in ['agen', 'import']:
			if not self.partner_id:
				raise exceptions.Warning('Apabila penggolongan AGEN/Import, Rekanan tidak boleh di kosongkan!')
				return
		
		#update status spm lines and return record id
		rec_id = 0
		res = {}
		res_model = ''
		
		if self.golongan in ['agen', 'import'] and self.pengadaan=="RD":
			res_model = 'logistik.spp'
			res = self.env.ref('ka_logistik_pengadaan.view_logistik_spp_form').id
			rec_id = self._create_spp()
			
		if self.golongan == 'agen' and self.pengadaan=='RP':
			res_model = 'purchase.order'
			res = self.env.ref('purchase.purchase_order_form').id
			rec_id = self._create_draft_po()

		if self.golongan == 'repeat':
			res_model = 'logistik.spp'
			res = mod_obj.get_object_reference('ka_logistik_pengadaan', 'view_logistik_spp_form')
			rec_id = self._create_repeat()

		if self.golongan == 'tender':
			res_model = 'logistik.tender'
			res = mod_obj.get_object_reference('ka_logistik_pengadaan', 'view_logistik_tender_form')
			rec_id = self._create_tender()
		
		res_id = res or False
		
		#redirect view
		return {
			'name': 'Open Form',
			'view_type': 'form',
			'view_mode': 'form',
			# 'view_id': [res_id],
			'res_model': res_model,
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'current',
			'res_id': rec_id[0].id, # and rec_id[0] or False,
		}

	@api.one
	def _create_spp(self):
		spm_line_ids = [l.spm_line_id.id for l in self.line_ids]
		tgl_diminta = min(self.line_ids, key=lambda x: x['tgl_minta'])['tgl_minta']
		lines = []
		nomor = self._generate_nomor_spp(self.spm_id.id)
		for line in self.line_ids:
			lines.append([0, 0, {
				'spm_line_id':line.spm_line_id.id,
				'product_id':line.product_id.id,
				'unit_id':line.unit_id.id,
				'kuantum':line.kuantum,
				'kuantum_sp':line.kuantum,
				'penyerahan': line.tgl_minta,
			}])
			
		vals = {
			'spm_id': self.spm_id.id,
			'no_spp': nomor,
			'partner_id': self.partner_id.id,
			'delivery_to': self.spm_id.operating_unit_id.id,
			'golongan': self.golongan,
			'tgl_serah': tgl_diminta,
			'line_ids': lines,
		}
		rec_id = self.env['logistik.spp'].create(vals) or None
		if rec_id:
			spm_line = self.env['logistik.spm.lines'].browse(spm_line_ids)
			for line in spm_line:
				line.write({'golongan': self.golongan})

		return rec_id

	@api.one
	def _create_tender(self):
		spm_line_ids = [l.spm_line_id.id for l in self.line_ids]
		tgl_diminta = min(self.line_ids, key=lambda x: x['tgl_minta'])['tgl_minta']
		lines = []
		nomor = self._generate_nomor_spp(self.spm_id.id)
		for line in self.line_ids:
			lines.append([0, 0, {
				'spm_line_id': line.spm_line_id.id, 
				'product_id': line.product_id.id, 
				'unit_id': line.unit_id.id, 
				'kuantum': line.kuantum,
				'pkrat_id': line.pkrat_id.id,
				'harga': 0,
				'total_harga': 0,
				'tgl_minta': line.tgl_minta,
			}])
			
		vals = {
			'nomor': nomor,
			'spm_id': self.spm_id.id,
			'tgl_tender': date.today().strftime('%Y-%m-%d'),
			'delivery_to': self.spm_id.operating_unit_id.id,
			'tgl_serah': tgl_diminta,
			'line_ids': lines,
		}

		rec_id = self.env['logistik.tender'].create(vals) or None
		if rec_id:
			spm_line = self.env['logistik.spm.lines'].browse(spm_line_ids)
			for line in spm_line:
				line.write({'golongan': self.golongan, 'state': self.golongan})
		return rec_id

	@api.one
	def _create_repeat(self):
		partner_id = None
		status = True
		for l in self.line_ids:
			pid = l.repeat_order_id.partner_id.id
			if partner_id == None:
				partner_id = pid
			elif partner_id != pid:
				status = False
				break

		if not status:
			raise exceptions.Warning('Partner ID salah')
			return
			
		spm_line_ids = [l.spm_line_id.id for l in self.line_ids]
		tgl_diminta = min(self.line_ids, key=lambda x: x['tgl_minta'])['tgl_minta']
		lines = []
		nomor = self._generate_nomor_spp(self.spm_id.id)
		for line in self.line_ids:
			lines.append([0, 0, {
				'spm_line_id':line.spm_line_id.id, 
				'product_id':line.product_id.id, 
				'unit_id':line.unit_id.id, 
				'kuantum':line.kuantum,
				'penawaran':line.price_unit,
				'harga':line.price_unit,
				'kuantum_sp':line.kuantum,
				'penyerahan': line.tgl_minta,
				'spm_line_id': line.spm_line_id.id,
				'keterangan': ('RO ' + line.repeat_order_id.name)
			}])
	
		vals = {
			'spm_id': self.spm_id.id,
			'no_spp': nomor,
			'partner_id': partner_id,
			'delivery_to': self.spm_id.operating_unit_id.id,
			'golongan': self.golongan,
			'tgl_serah': tgl_diminta,
			'line_ids': lines,
		}
		
		rec_id = self.env['logistik.spp'].create(vals) or None
		if rec_id:
			spm_line = self.env['logistik.spm.lines'].browse(spm_line_ids)
			for line in spm_line:
				line.write({'golongan': self.golongan, 'state':'draftsp'})
		
		return rec_id
	
	@api.one
	def _create_draft_po(self):
		''' 
		Merealisasikan SPM menjadi SP(Surat Pesanan)
			Call From	: Penggolongan SPM
			Return		: Wndows Action`
			Parameter
		'''
		spm_line_ids = []
		lines = []
		new_order = None
		for line in self.line_ids:
			spm_line_ids.append(line.spm_line_id.id)
			product_desc = (line.product_id.name or '') + '\n' + (line.product_id.description or '')
			if not line.product_id:
				product_desc = line.product_description
			lines.append([0, 0, {
				'product_id':line.product_id.id, 
				'name': product_desc,
				'product_uom':line.unit_id.id, 
				'product_qty': line.kuantum,
				'price_unit': 0,
				'account_analytic_id':line.spm_line_id.pkrat_id.account_analytic_id.id,
				'date_planned':line.tgl_minta,
				'spm_line_id': line.spm_line_id.id,
				'pengadaan': self.pengadaan,
			}])

		# sp = False
		if lines:
			ttd_dir = self.company_id.dept_dirut.manager_id.id
			ttd_keu = self.company_id.dept_dirkeu.manager_id.id 
			ttd_log = self.company_id.dept_log.manager_id.id 
			order_no = self.env['ir.sequence'].next_by_code('purchase.order')				
			vals = {
				'name': order_no,
				'partner_id': self.partner_id.id,
				'operating_unit_id': self.company_id.partner_id.id,
				'golongan': self.golongan,
				'ttd_dir': ttd_dir,
				'ttd_keu': ttd_keu,
				'ttd_log': ttd_log,
				'order_line': lines,
				'date_planned': min(self.line_ids, key=lambda x: x['tgl_minta'])['tgl_minta']
			}
			new_order = self.env['purchase.order'].create(vals)
			if new_order:
				spm_lines = self.env['logistik.spm.lines'].browse(spm_line_ids)
				for spm_line in spm_lines:
					spm_line.write({'golongan' :self.golongan, 'state': 'draftsp'})
				
				return new_order

	def _generate_nomor_spp(self, spm_id):
		nomor = ''
		no_spm = self.env['logistik.spm'].browse(spm_id)['no_spm']
		tender_ids = self.env['logistik.tender'].search([('spm_id', '=', spm_id)])
		spp_ids = self.env['logistik.spp'].search([('spm_id', '=', spm_id)])
		no_seq = len(tender_ids) + len(spp_ids) + 1
		nomor = "%s/%02d" % (no_spm, no_seq)
		return nomor