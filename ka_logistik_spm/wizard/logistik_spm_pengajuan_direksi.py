from odoo import models, fields, api

class logistik_spm_pengajuan_direksi(models.TransientModel):
	_name = 'logistik.spm.pengajuan.direksi'
	_description = "Wizard Pengajuan SPM ke Direksi"
	
	nomor = fields.Char(string='Nomor SPM', size=12, default='/')
	tanggal = fields.Date(string='Tanggal', required=True, default=fields.Date.today)
	company_id = fields.Many2one('res.company', string='Unit/PG', default=lambda self: self.env['res.company']._company_default_get(self._name))
	line_ids = fields.One2many('logistik.spm.pengajuan.direksi.line', 'spm_id', string='Detail Barang', states={'draft': [('readonly', False)]})
	note = fields.Text(string='Catatan')
	category = fields.Selection([
		('none','Belum Dikategorikan'),
		('rab','RAB'),
		('nonrab','Non RAB'),
		('noncode','Tanpa Kode'),
	], string='Jenis SPM', required=True)

	@api.model
	def default_get(self, fields_list):
		if self._context.get('company_id', False):
			company_id = self._context['company_id']
		else:
			company_id = self.env['res.users'].browse(self._uid).company_id.id
			
		category = self._context.get('category', False)
		res = super(logistik_spm_pengajuan_direksi, self).default_get(fields_list)
		spm_lines = self.env['logistik.spm.lines'].search([('category', '=', category), ('company_id', '=', company_id), ('spm_id', '=', False), ('state', '=', 'validated'), ('btn_test', '!=', 'reject')])
		# spm_lines = self.env['logistik.spm.lines'].search([('category', '=', category), ('company_id', '=', company_id), ('spm_id', '=', False), ('state', '=', 'approved')])
		lines = []
		for spm_line in spm_lines:
			if spm_line.pengadaan == 'RD':
				line = {
					'rec_id' : spm_line.id,
					'product_id' : spm_line.product_id.id,
					'spesifikasi' : spm_line.spesifikasi,
					'kuantum' : spm_line.kuantum,
					'tgl_minta' : spm_line.tgl_minta,
					'account_id' : spm_line.account_id.id,
					'pkrat_id' : spm_line.pkrat_id.id,
					'stasiun_id' : spm_line.stasiun_id.id,
					'selected': True,
					'pengajuan_id': spm_line.pengajuan_id.id,
				}
				lines.append((0,0,line))

		res.update(
			category = category,
			line_ids = lines
		)

		return res

	@api.multi
	def do_create_spm_direksi(self):
		self.ensure_one()
		if not self.line_ids:
			return
		
		nomor = self.env['logistik.spm'].get_nomor_spm(self.category, self.tanggal)		

		line_ids = [line.rec_id for line in self.line_ids if line.selected==True]
		spm_lines = self.env['logistik.spm.lines'].browse(line_ids)
		
		vals = {
			'no_spm': nomor,
			'tanggal': self.tanggal,
			'pengadaan': 'RD',
			'category': self.category,
			'company_id': self.company_id.id,
			'state': 'validated',
			# 'line_ids': line_ids,
		}
		spm = self.env['logistik.spm'].create(vals)
		spm_name = spm.get_name(spm.parent_id, spm.no_spm, spm.split_no)
		spm.write({'name': spm_name})
		spm.action_number()
		for line in spm_lines:
			line.link_to_spm(spm.id)

		#open form SPM
		return {
			'name': 'Open Form',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'logistik.spm',
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'current',
			'res_id': spm.id,
		}