# ----------------------------------------------------------
# Data Detail SPP (Surat Permintaan Pesanan)
# order sorting 'harga'
# ----------------------------------------------------------

from odoo import models, fields, api, exceptions

class logistik_spp_lines(models.Model):
	_name = 'logistik.spp.lines'
	_description = "LOG1G3 - Detail Harga SPP"
	_order = "harga asc"

	spp_id = fields.Many2one('logistik.spp', string='No. SPP', required=True, ondelete='cascade')
	partner_id = fields.Many2one(related='spp_id.partner_id', string='Rekanan', readonly=True)
	product_id = fields.Many2one('product.product', string='Kode Barang', required=True)
	spesifikasi =  fields.Text(related='product_id.description', string='Spesifikasi', readonly=True)
	unit_id = fields.Many2one('product.uom', string='Satuan')
	penyerahan = fields.Date(string='Tgl. Serah', help='Tanggal Penyerahan yang diharapkan!')
	waktu_kirim = fields.Integer(string='Waktu (Hari)')
	kuantum = fields.Float(string='Kuantum', digits=(11, 2), required=True)
	kuantum_sp = fields.Float(string='Kuantum SP', digits=(11, 2), required=True)
	penawaran = fields.Float(string='Penawaran', digits=(16, 2))
	harga = fields.Float(string='Harga Nego', digits=(16, 2))
	total_tawar = fields.Float(compute='_compute_total_tawar', string='Total Harga', digits=(16, 2), store=True)
	total_harga = fields.Float(compute='_compute_total_harga', string='Total Harga', digits=(16, 2), store=True)
	lst_price = fields.Float(related='product_id.lst_price', store=True, string='HPS', readonly=True)
	tender_line_id = fields.Many2one('logistik.tender.lines', string='Barang Tender') 
	spm_line_id = fields.Many2one('logistik.spm.lines', string='SPM Line')
	menang = fields.Boolean(string='Menang')
	keterangan = fields.Char(string='Keterangan', size=64)
	company_id = fields.Many2one(string='Perusahaan', related='spp_id.company_id', store=True, readonly=True)

	@api.depends('kuantum', 'harga')
	def _compute_total_harga(self):
		"""
		Computing 'total_harga', depends 'kuantum' & 'harga'
		"""
		for s in self:
			s.total_harga = s.kuantum * s.harga

	@api.depends('kuantum', 'penawaran')
	def _compute_total_tawar(self):
		"""
		Computing 'total_tawar', depends 'kuantum' & 'penawaran'
		"""
		for s in self:
			s.total_tawar = s.kuantum * s.penawaran

	@api.multi
	def action_open_histori_harga(self):
		"""
		Open histori harga yg pernah ditenderkan
		"""
		mod_obj = self.env['ir.model.data']
		res = mod_obj.get_object_reference('ka_logistik_pengadaan', 'view_open_histori_harga')
		res_id = res and res[1] or False
		return {
			'name': 'Histori Harga',
			'view_type': 'form',
			'view_mode': 'tree',
			'context': self._context,
			'view_id': [res_id],
			'limit': 10,
			'domain': [('product_id', '=', self.product_id.id)],
			'res_model': 'purchase.order.line',
			'type': 'ir.actions.act_window',
			'target': 'new',
		}

	@api.one
	def action_set_winner(self):
		"""
		Set 'menang' = not status.menang & update record
		"""
		self.write({'menang': not status.menang})
	
	@api.onchange('harga', 'penawaran')
	def onchange_harga(self):
		print self.harga, self.penawaran
		print "<<<<<<<<<<<<<<<<<<<<<<<<<"