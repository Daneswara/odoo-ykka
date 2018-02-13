from odoo import models, fields, api, exceptions

class logistik_pengajuan_spm(models.Model):
	_name = 'logistik.pengajuan.spm'
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_description = 'Pengajuan SPM'
	_rec_name = 'nomor'
	_order = 'tanggal desc'

	
	def _get_department_by_user(self):
		res = None
		employee = self.env.user._get_related_employees()
		if employee:
			dept = employee.department_id
			if dept.parent_id and dept.parent_id.parent_id:
				res = dept.parent_id.id
		return res		
	
	nomor = fields.Char(string='Nomor Permintaan', size=12, readonly=False, required=True, copy=False, default='Draft SPM')
	tanggal = fields.Date(string='Tanggal SPM', required=True, readonly=False, default=fields.Date.today, copy=False)
	department_id = fields.Many2one('hr.department', string='Bagian', required=True, domain="[('company_id', '=', company_id)]", states={'draft': [('readonly', False)]}, default=_get_department_by_user)
	seksi_id = fields.Many2one('hr.department', string='Seksi', domain="[('parent_id', '=', department_id)]", required=True, states={'draft': [('readonly', False)]})
	tgl_minta =  fields.Date(string='Tgl Diminta', required=False, copy=False)
	line_ids = fields.One2many('logistik.spm.lines', 'pengajuan_id', string='Detail Barang', domain=[('parent_id', '=', False)], states={'draft': [('readonly', False)]}, copy=True)
	operating_unit_id = fields.Many2one('res.partner', required=True, string="Unit/PG", 
        domain=[('is_operating_unit', '=', True)], 
        default=lambda self: self.env['res.users'].operating_unit_default_get(self._uid))
	company_id = fields.Many2one('res.company', string='Perusahaan', required=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env['res.company']._company_default_get('logistik.pengajuan.spm'))
	user_id = fields.Many2one('res.users', string='Dibuat Oleh', readonly=True, default=lambda self: self._uid, copy=False)
	state = fields.Selection([
		('draft', 'Draft'),
		('propose', 'Validate'),
		('printed', 'Printed'),
		('confirm', 'Gudang OK'),
		('wait', 'Tunggu Persetujuan'),
		('approved', 'Approve'),
		('cancel', 'Cancel'),
		],'Status', readonly=True, default='draft', track_visibility='onchange', 
		help="Konsep: Masih Bisa Dikoreksi,\
			Validate: Siap Untuk Cetak,\
			Printed: Sudah tercetak dan Tunggu Konfirmasi Gudang,\
			Gudang OK: Sudah Verifikasi Gudang,\
			Tunggu Persetujuan: Tunggu Persetujuan Pemimpin Pabrik,\
			Approve: Sudah disetujui Pempimpn, dan Proses Pengadaan oleh Logistik")
	pengadaan = fields.Selection([
		('RD', 'Direksi'),
		('RP', 'Pabrik'),
	], string='Jenis SP')
	note = fields.Text(string='Catatan')
	product_id = fields.Many2one('product.product', 'Produk', related='line_ids.product_id')

	
	def _get_noline_exceptions(self):
		raise exceptions.Warning('Item barang harus diisi!')

	def _check_field_value(self, vals, field_name):
		if not vals.has_key(field_name) or not vals[field_name]:
			return False
		return True

	# @api.model
	# def create(self, vals):
		# if not vals.has_key('line_ids') or not vals['line_ids']:
			# self._get_noline_exceptions()
			# return
		# return super(logistik_pengajuan_spm, self).create(vals)

	@api.multi
	def write(self, vals):
		if vals.has_key('line_ids') and not vals['line_ids']:
			self._get_noline_exceptions()
			return
		return super(logistik_pengajuan_spm, self).write(vals)

	# @api.onchange('company_id')
	# def onchange_company_id(self):
		# for s in self:
			# s.department_id = None

	@api.onchange('department_id')
	def onchange_department_id(self):
		employee = self.env.user._get_related_employees()
		if employee:
			self.seksi_id = employee.department_id.id

	@api.multi
	def action_report(self):
		return self.env['report'].get_action(self, 'ka_logistik_spm.report_pengajuan_spm')
	
	@api.multi
	def action_propose(self):
		if not self.line_ids:
			self._get_noline_exceptions()
			return

		nomor = self.nomor
		if self.nomor == 'Draft SPM':
			if not self.department_id.sequence_id:
				raise exceptions.Warning('Penomoran untuk Bagian Tersebut belum dibuatkan. Silahkan menghubungi PDE/Administrator!')
			nomor = self.department_id.sequence_id.next_by_id()
			
		for line in self.line_ids:
			line.action_propose()

		self.write({'nomor': nomor, 'state': 'propose'})

	@api.multi
	def action_print(self):
		for this in self:
			if this.state == 'propose':
				# if status = validate, then change to printed & send notification
				this.state = 'printed'
				for line in this.line_ids:
					line.action_print()
				#### send message notification to users ####
				follower_ids = [follower.partner_id.id for follower in this.message_follower_ids]
				mail_to_ids = []
				for partner in self.env.user.company_id.verifikasi_kode_barang_partners_ids:
					if partner.id not in follower_ids:
						mail_to_ids.append(partner.id)
						follower_ids.append(partner.id)
						
				if mail_to_ids != []:
					# change status and add followers in records, in order to get notification in their inbox	
					followers = [(0,0,{'res_model': self._name, 'subtype_ids': [(4, self.env.ref('mail.mt_comment').id)], 'partner_id': pid}) for pid in mail_to_ids]
					this.write({'message_follower_ids': followers})
					
				# send message
				email = self.env.ref('ka_logistik_spm.template_notif_print_spm')
				post_vars = {'message_type': 'notification', 'message_subtype': 'mt_comment', 'partner_ids': follower_ids}
				this.message_post_with_template(email.id, **post_vars)
			return this.action_report()
	
	@api.multi
	def action_wait(self):
		self.state='wait'
		
	@api.one
	def action_draft(self):
		if self.create_uid.id <> self._uid:
			raise exceptions.Warning('Pengaturan menjadi konsep hanya dapat dilakukan oleh user bersangkutan')
			return

		if self.state == 'approved':
			raise exceptions.Warning('Pengajuan yang sudah diproses bagian logistik tidak dapat dikembalikan menjadi Konsep')
			return
			
		self.write({'state': 'draft'})
		for line in self.line_ids:
			line.action_draft()

	@api.one
	def action_cancel(self):
		if self.state == 'approved':
			raise exceptions.Warning('Pengajuan yang sudah dikonfirmasi bagian logistik tidak dapat dibatalkan')
			return

		self.write({'state': 'cancel'})
		for line in self.line_ids:
			line.action_cancel()

	@api.one
	def action_confirm(self):
		for line in self.line_ids:
			if line.btn_test != 'reject':
				line.action_confirm()
		self.write({'state': 'confirm'})

	@api.one
	def action_approve(self):
		for line in self.line_ids:
			if line.state != 'cancel':
				if line.btn_test != 'reject':
					if self.pengadaan == 'RD':
						if not line.account_id:
							raise exceptions.Warning('No. Perkiraan belum diisi!')
							return
						if not line.category:
							raise exceptions.Warning('Jenis SPM belum diisi!')
							return
						if not line.pengadaan:
							raise exceptions.Warning('Pengadaan belum diisi!')
							return
						if not line.kuantum:
							raise exceptions.Warning('Jumlah setuju belum diisi!')
							return
						if line.kuantum_spm < line.kuantum and not line.alasan:
							raise exceptions.Warning('Alasan belum disii!')
						line.action_validate()

					else:
						line.action_approve()
		self.write({'state': 'approved'})

	@api.multi
	def unlink(self):
		if self.state != 'draft':
			raise exceptions.Warning('Selain konsep, permintaan tidak dapat dihapus!')
			return

		if self.create_uid.id <> self._uid:
			raise exceptions.Warning('DELETE SPM hanya dapat dilakukan oleh user bersangkutan')
			return

		return super(logistik_pengajuan_spm, self).unlink()