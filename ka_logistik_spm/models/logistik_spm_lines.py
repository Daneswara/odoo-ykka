from odoo.exceptions import UserError
from odoo.exceptions import UserError
from odoo import models, fields, api, exceptions

class logistik_spm_lines(models.Model):
	_name = 'logistik.spm.lines'
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_description = "Detail SPM"
	_order = "tgl_minta, id asc"
	_rec_name = "name"
				
	@api.multi
	def _compute_name(self):
		for s in self:
			ret_name = s.pengajuan_id.nomor
			if s.spm_id:
				ret_name = '%s / %s' % (s.pengajuan_id.nomor,s.spm_id.no_spm)
			s.name = ret_name

	spm_id = fields.Many2one('logistik.spm', string='SPM Direksi', readonly=True)
	pengajuan_id = fields.Many2one('logistik.pengajuan.spm', string='Nomor Permintaan', readonly=True, ondelete='cascade')
	name =  fields.Char(string='Nomor SPM', compute='_compute_name')
	tanggal_spm = fields.Date(string='Tgl. SPM', related='spm_id.tanggal', store=True, readonly=True)
	operating_unit_id = fields.Many2one('res.partner', required=True, string="Unit/PG", 
        domain=[('is_operating_unit', '=', True)], 
        default=lambda self: self.env['res.users'].operating_unit_default_get(self._uid))
	company_id = fields.Many2one('res.company', string='Perusahaan', required=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env['res.company']._company_default_get('logistik.spm.lines'))
	stasiun_id = fields.Many2one('account.analytic.stasiun', string='Stasiun', required=True)
	account_id = fields.Many2one('account.account', string='No. Perkiraan')
	rab_id = fields.Many2one('logistik.rab', string='Perkiraan di-RAB', help='Nomor RAB/Perkiraan yang terdaftar Rencana Pemakaian')
	product_id = fields.Many2one('product.product', string='Kode & Nama Barang', track_visibility='onchange')
	product_qoh = fields.Float('Saldo', compute='compute_product_qoh')
	product_desc = fields.Text(string='Spesifikasi', related='product_id.description', readonly=True)
	rab_prod = fields.Many2one('logistik.rab.lines', string='Kode Barang di-RAB')
	unit_id =  fields.Many2one('product.uom', string='Satuan', related='product_id.uom_id', readonly=True)
	spesifikasi = fields.Text(string='Spek Yang Diminta')
	pabrikan = fields.Char(string='Pabrikan', related='product_id.pabrikan', size=15, help="Nama pabrik pembuat barang")
	kuantum_spm = fields.Float(string='Jml Diminta', digits=(11, 2), required=True, default=0.0) # diinput oleh user
	kuantum =  fields.Float(string='Jml Setuju', digits=(11, 2), required=True, track_visibility='onchange', default=0.0) #disetujui TUK
	kuantum_sp = fields.Float(string='Kuantum SP', digits=(11, 2), required=True, track_visibility='onchange', default=0.0) #disetujui DIV-DIR
	qty_realisasi = fields.Float(compute='_compute_qty', store=True, digits=(11, 2), string='Realisasi', readonly=True)
	qty_saldo = fields.Float(compute='_compute_qty', store=True, string='Saldo SPM', digits=(11, 2), readonly=True)	# jumlah total yg belum direalisasikan oleh semua child
	tgl_minta = fields.Date(string='Tgl.Diminta', required=False, track_visibility='onchange')
	pkrat_id = fields.Many2one('logistik.pkrat', string='No. Investasi', track_visibility='onchange')
	pkrat_name =  fields.Char(string='Nama Proyek', related='pkrat_id.name', readonly=True)
	name_spec =  fields.Text(compute='_compute_name_spec', string='Nama dan Spesifikasi Barang')
	product_name_desc = fields.Text('Nama & Spesifikasi Barang', compute='get_product_name_desc', store=True, help='Field untuk pencarian kode, nama, spesifikasi barang atau spesifikasi yang diminta')
	pengadaan = fields.Selection([
		('RD', 'Direksi'),
		('RP', 'Pabrik')
	], string='Pengadaan', default='RD')
	# category = fields.Selection(related='spm_id.category', string='Jenis SPM')
	category = fields.Selection([
		('rab', 'RAB'),
		('nonrab', 'Non RAB'),
		('noncode', 'Tanpa Kode')
	], string='Jenis SPM')
	golongan = fields.Selection([
		('none', 'Belum digolongkan'),
		('import', 'Import'),
		('tender', 'Tender'),
		('agen', 'Agen'),
		('repeat', 'Repeat'),
	], string='Golongan', default='none')
	catatan = fields.Text(string='Catatan/Keperluan')
	alasan = fields.Char(string='Alasan', size=128, track_visibility='onchange')
	state = fields.Selection([
		('draft', 'Draft'),
		('propose', 'Penomoran'),
		('print', 'Printed'),		
		('confirm', 'Gudang OK'),			#Verifikasi Gudang
		('validated', 'Validate TUK'),		#validate by TUK PG
		('spm', 'SPM Direksi'), 			#ketika permintaan sudah di kategorikan RAB. non RAB atau Tanpa Kode
		('approved', 'Approve'),			#validate by Direksi Divisi Terkait
		('tender', 'Tender'),
		('draftsp', 'Proses SP'),
		('sp', 'Sudah SP'),
		('receive', 'Diterima'),
		('done', 'Selesai'),
		('cancel', 'Di-Batalkan'),
	], string='Status', readonly=False, default='draft', track_visibility='onchange')
	btn_test = fields.Selection([
		('draft', 'Konsep'),
		('print', 'Pengajuan'),
		('validated', 'Di-Validasi'),
		('approved', 'Di-Setujui'),
		('reject', 'Di-Batalkan'),
	], string='Status Sementara', default='draft')
	spm_state = fields.Selection(related='spm_id.state', selection=[
		('draft', 'Konsep'),
		('validated', 'Di-Validasi'), 	#By TUK - PG
		('approved', 'Di-Setujui'),		#by Direksi
		('reject', 'Di-Batalkan')
	], string='Status SPM', readonly=True)
	parent_id = fields.Many2one('logistik.spm.lines', string='SPM Asal')
	child_ids = fields.One2many('logistik.spm.lines', 'parent_id', string='Realisasi')
	gambar = fields.Binary('Contoh Gambar')
	doc_count = fields.Integer(compute='_get_attached_docs', string='Number of documents attached')
	department_id = fields.Many2one(string="Bagian", related='pengajuan_id.department_id', store=True)
	seksi_id = fields.Many2one(string="Seksi", related='pengajuan_id.seksi_id', store=True)
	request_code_sent = fields.Boolean(compute='_get_request_code_check', string='Request Sent')
	
	@api.one
	def compute_product_qoh(self):
		quant_src = self.env['stock.quant'].search([('product_id','=',self.product_id.id),
													('company_id','=',self.company_id.id),
													('location_id.usage','=','internal')])
		self.product_qoh = sum(quant.qty for quant in quant_src)

	#@api.multi
	@api.depends('child_ids', 'kuantum_sp', 'kuantum')
	def _compute_qty(self):
		for spm_line in self:
			realisasi = sum(l.kuantum_sp for l in spm_line.child_ids) + spm_line.kuantum_sp
			spm_line.qty_saldo = spm_line.kuantum - realisasi
			spm_line.qty_realisasi = realisasi

	@api.multi
	@api.depends('product_id','spesifikasi')
	def _compute_name_spec(self):
		for s in self:
			if not s.product_id:
				s.name_spec = s.spesifikasi
			else:
				name = s.product_id.default_code + ' - ' if s.product_id.default_code else ''
				name += s.product_id.name if s.product_id.name else ''
				s.name_spec = name + '\n' + (s.product_id.description or '')
	
	@api.multi
	@api.depends('product_id','product_id.description','spesifikasi')
	def get_product_name_desc(self):
		for this in self:
			name = this.product_id.default_code + ' - ' if this.product_id.default_code else ''
			name += this.product_id.name if this.product_id.name else ''
			name += '\n' + (this.product_id.description or '')
			name += '\n' + (this.spesifikasi or '')
			this.product_name_desc = name

	@api.model
	def _get_attached_docs(self):
		attachment = self.env['ir.attachment']
		for s in self:
			doc_attachments = attachment.search([('res_model', '=', s._name), ('res_id', '=', s.id)], count=True)
			s.doc_count = (doc_attachments or 0)

	@api.multi
	def attachment_tree_view(self):
		ids = [s.id for s in self]
		domain = [('res_model', '=', self._name), ('res_id', 'in', ids)]
		res_id = ids and ids[0] or False
		return {
			'name': 'Attachments',
			'domain': domain,
			'res_model': 'ir.attachment',
			'type': 'ir.actions.act_window',
			'view_id': False,
			'view_mode': 'kanban,tree,form',
			'view_type': 'form',
			'limit': 80,
			'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, res_id)
		}
	
	@api.multi
	def link_to_spm(self, spm_id):
		return self.write({'state': 'spm', 'spm_id': spm_id})
		
	# def action_validate_xxxxx(self, cr, uid, ids, context=None):
	# 	lines = self.browse(cr, uid, ids, context)
	# 	for line in lines:
	# 		self.write(cr, uid, line.id, {'state': line.btn_test}, context)
	# 	return 

	@api.one
	def action_print(self):
		vals = {'state': 'print'}
		if self.pengajuan_id:
			vals['pengadaan'] = self.pengajuan_id.pengadaan
		return self.write(vals)

	@api.one
	def action_draft(self):
		return self.write({'state': 'draft'})

	@api.one
	def action_cancel(self, data=None):
		# set allowed users : creator of pengajuan SPM, kabag, logistik
		allowed_users = [self.pengajuan_id.create_uid.id]
		kabag_id = self.pengajuan_id.department_id.manager_id.user_id.id
		if kabag_id:
			allowed_users.append(kabag_id)
		for logistik in self.env.user.company_id.logistik_user_ids:
			allowed_users.append(logistik.id)
		if self._uid not in allowed_users:
			raise exceptions.Warning('Pembatalan SPM hanya dapat dilakukan oleh user bersangkutan, Kepala Bagian, atau Logistik')
			return
		write_vals = {'state': 'cancel'}
		if data and not isinstance(data, dict) and data.cancel_reason:
			write_vals['alasan'] = data.cancel_reason
		self.write(write_vals)
	
	@api.one
	def action_spm_direksi(self):
		# if self.kuantum_sp == 0.00:
			# self.kuantum_sp = self.kuantum
		self.write({'state': 'spm'})            
		post_vars = {'subject': "SPM Baru", 'body': "SP Direksi Baru", 'partner_ids': [(6017)],}
		self.message_post(type="notification", subtype="mt_comment", **post_vars)
	
	@api.one
	def action_approve(self):
		return self.write({'state': 'approved'})

	@api.one
	def action_confirm(self):
		return self.write({'state': 'confirm'})

	@api.one
	def action_validate(self):
		return self.write({'state': 'validated'})

	@api.one
	def action_propose(self):
		return self.write({'state': 'propose'})

	@api.one
	def action_receive(self):
		return self.write({'state': 'receive'})

	@api.one
	def action_done(self):
		return self.write({'state': 'done'})

	@api.one
	def action_undo_realisasi(self):
		if not self.parent_id:
			return self.write({'state':'spm', 'kuantum_sp': 0.0})
		else:
			# dict(self._context).update({'force_unlink': True})
			self.with_context(force_unlink=True).unlink()
			# return self.reload_tree_view()
			return {'type': 'ir.actions.act_window_close'}
	
	@api.one
	def action_realisasi_all(self):
		return self.write({'state': 'approved', 'kuantum_sp': self.qty_saldo})

	@api.one
	def action_realisasi_bertahap(self, vals):
		#create realisasi spm line baru
		default = {
			'parent_id': vals['parent_id'],
			'kuantum':vals['kuantum_sp'],
			'kuantum_sp':vals['kuantum_sp'],
			'alasan':vals['alasan'],
			'state': 'approved',
		}
		return self.copy(default)
	
	# def reload_tree_view(self, cr, uid, ids, context):
	# 	return {'type': 'ir.actions.act_window_close'}
	# 	mod_obj = self.pool.get('ir.model.data')
	# 	views = mod_obj.get_object_reference(cr, uid, 'logistik_spm', 'view_logistik_spm_lines_approve_tree')
	# 	return {
	# 		'name': 'Persetujuan SPM dari PG',
	# 		'view_type': 'form',
	# 		'view_mode': 'tree',
	# 		'view_id': views[1],
	# 		'res_model': 'logistik.spm.lines',
	# 		'type': 'ir.actions.act_window',
	# 		'nodestroy': True,
	# 		'domain':"[('state', 'in', ('spm', 'approved')), ('pengadaan', '=', 'RD')]",
	# 		'target': 'new',
	# 	}

	@api.one
	def action_reject(self):
		return self.write({'btn_test':'reject'})
	
	# #SPM hanya dapat di hapus, apabila belum digolongkan
	@api.multi
	def unlink(self):
		unlink_ids = []
		for s in self:
			if s.state == 'draft' or s._context.get('force_unlink', False):
				unlink_ids.append(s.id)
			else:
				raise exceptions.Warning('SPM yang sudah di setujui tidak dapat dihapus!')
		if len(unlink_ids) > 0:
			return super(logistik_spm_lines, self).unlink()

	@api.onchange('seksi_id')
	def onchange_department(self):
		stasiun = self.env['account.analytic.stasiun'].search([('department_id', '=', self.seksi_id.id)])
		if stasiun:
			self.stasiun_id = stasiun[0].id

	@api.onchange('product_id')
	def onchange_product(self):
		# product_line=self.search([('product_id', '=', self.product_id.id), ('spm_id', '=', self.spm_id.id), ('stasiun_id', '=', self.stasiun_id.id)], limit=1)
		# print self.product_id, self.spm_id, self.stasiun_id
		# if product_line:
			# raise UserError('PERHATIAN :  Ada kesamaan barang')
		if self.category <> 'noncode':
			self.spesifikasi = self.product_id.description
			
	# @api.onchange('kuantum')
	# def onchange_kuantum(self):
		# self.kuantum_sp = self.kuantum
		
	@api.multi
	def _get_request_code_check(self):
		for line in self:
			request = self.env['spm.product.code.request'].search([('spm_line_id', '=', line.id)])
			sent = len(request) > 0
			line.request_code_sent = sent
		
	def action_product_code_request(self):
		request = self.env['spm.product.code.request'].search([('spm_line_id', '=', self.id)])
		if request:
			raise exceptions.Warning('Permintaan Kode Barang sudah pernah dibuat')
			return
		
		mod_obj = self.env['ir.model.data']
		res = mod_obj.get_object_reference('ka_logistik_spm', 'view_product_code_request_form')
		view_id = res and res[1] or False
		return {
			'name': 'Permintaan Kode Barang Baru',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'spm.product.code.request',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'nodestroy': False,
			'view_id': [view_id],
			'context':{'default_spm_line_id': self.id, 'default_name': self.spesifikasi},
			'flags': {'form': {'action_buttons': False, 'options': {'mode': 'edit'}}},
		}
		
	@api.multi
	def send_notification_edit_pengadaan(self, reason):
		for line in self:           
			# followers  
			follower_id = False
			for follower in line.message_follower_ids:
				if follower.partner_id.id == line.pengajuan_id.user_id.partner_id.id:
					follower_id = follower.id
					break
			followers = [(1, follower_id, {'subtype_ids': [(4, self.env.ref('ka_logistik_spm.mt_pengajuan_spm_edit_pengadaan').id)]})]
			line.write({'message_follower_ids': followers})
			# send message
			partner_ids = [line.pengajuan_id.user_id.partner_id.id]
			email = self.env.ref('ka_logistik_spm.template_notif_edit_jenis_spm')
			base_template = email.body_html
			content = '''%s'''%(email.body_html)
			body_message = content%(reason)
			email.write({'body_html': body_message})
			post_vars = {'message_type': 'notification',
	                     'subtype_id': self.env.ref('ka_logistik_spm.mt_pengajuan_spm_edit_pengadaan').id,
	                     'needaction_partner_ids': partner_ids}
			line.message_post_with_template(email.id, **post_vars)
			email.write({'body_html': base_template})
	
	