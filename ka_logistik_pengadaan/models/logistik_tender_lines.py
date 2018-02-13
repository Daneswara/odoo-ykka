# ----------------------------------------------------------
# Data Detail Pengadaan (Tender)
# order sorting 'product_id'
# ----------------------------------------------------------

from odoo import models, fields, api, exceptions

class logistik_tender_lines(models.Model):
	_name = 'logistik.tender.lines'
	_description = "Logistik Tender Lines"
	_rec_name = 'product_id'
	_order = 'product_id'

	tender_id = fields.Many2one('logistik.tender', string='Nomor SPP', required=True, ondelete='cascade')
	product_id = fields.Many2one('product.product', string='Kode Barang', required=True)
	spesifikasi = fields.Text(related='product_id.description', string='Spesifikasi', readonly=True)
	pkrat_id = fields.Many2one('logistik.pkrat', string='No. Investasi')
	unit_id = fields.Many2one('product.uom', string='Satuan')
	kuantum = fields.Float(string='Kuantum', digits=(11, 2), required=True)
	tgl_minta = fields.Date(string='Tgl. Diminta')
	lst_price = fields.Float(related='product_id.lst_price', string='HPS', readonly=True)
	spp_line_ids = fields.One2many('logistik.spp.lines', 'tender_line_id', string='Penawaran Harga')
	keterangan = fields.Char(string='Keterangan', size=64)
	spm_line_id = fields.Many2one('logistik.spm.lines', string='SPM Line')
	winner_info = fields.Char(compute='_compute_winner', string='Pemenang')
	winner_qty = fields.Float(compute='_compute_winner', digits=(11, 2), string='Kuantum SP')
	state = fields.Selection(related='tender_id.state', store=True, selection=[
		('draft', 'Konsep'),
		('spp', 'SPPH'),
		('wait', 'Tunggu Persetujuan'),
		('approved', 'Di-Setujui'),
		('sp', 'Sudah SP'),
		('cancel', 'Di-Batalkan')
	], string='Status')

	"""
	Flag status winner, klo sudah _compute_winner maka status True & _compute hanya dijalankan 1 kali
	"""
	_status_compute_winner = False

	@api.multi
	def _compute_winner(self):
		"""
		Compute 'winner_info' & 'winner_qty'
		"""
		if self._status_compute_winner:
			return

		_status_compute_winner = True

		for s in self:
			winner_info = ''
			for spp_line in s.spp_line_ids:
				if spp_line.menang:
					winner_info += spp_line.partner_id.code + ' - '
			s.winner_info = winner_info[:-3]

			product_id = s.product_id.id
			s.winner_qty = sum(spp_line.kuantum_sp for spp_line in s.spp_line_ids if spp_line.product_id.id == product_id and spp_line.menang)

	@api.multi
	def action_open_ranking(self):
		"""
		Open ranking pemenang tender
		"""
		harga = sum(spp.total_harga for spp in self.spp_line_ids)
		if harga == 0:
			raise exceptions.Warning('Harga Rekanan belum diterima / dientry. Masukkan harga terlebih dahulu dengan memilih Klik PESERTA TENDER kemudian Klik SPPH')
			return

		#redirect view
		return {
			'name': 'Pemilihan Pemenang Tender',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': self._name,
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'new',
			'flags': {'form': {'action_buttons': False, 'options': {'mode': 'edit'}}},
			'res_id': self.id, # and rec_id[0] or False,
		}

	@api.multi
	def unlink(self):
		"""
		Unlink spp_line in 'spp_line_ids'
		Set logistik.spm 'spm_line_id', 'state': 'approved', 'golongan': 'none'
		update record
		unlink self
		"""
		for tender_line in self:
			for spp_line in tender_line.spp_line_ids:
				if spp_line.product_id == tender_line.product_id and spp_line.spm_line_id == tender_line.spm_line_id:
					spp_line.unlink()

			tender_line.spm_line_id.write({'state': 'approved', 'golongan': 'none'})

		return super(logistik_tender_lines, self).unlink()
	
	@api.multi
	def action_open_histori_harga(self):
		"""
		Open histori harga
		"""
		mod_obj = self.env['ir.model.data']
		res = mod_obj.get_object_reference('ka_logistik_pengadaan', 'view_open_histori_harga')
		res_id = res and res[1] or False
		return {
			'name': 'Histori Harga',
			'view_type': 'form',
			'view_mode': 'tree',
			'context': self._context,
			'limit': 10,
			'view_id': [res_id],
			'domain': [('product_id', '=', self.product_id.id)],
			'res_model': 'purchase.order.line',
			'type': 'ir.actions.act_window',
			'target': 'new',
		}

	# @api.one
	def get_last_sp(self, prod_id, date_order):
		"""
		History harga berdasarkan sp terakhir
		"""
		res = self.env['purchase.order.line'].search([('product_id', '=', prod_id), ('tanggal_sp', '<', date_order)], limit = 3, order = 'tanggal_sp desc')
		return res