from odoo import models, fields, api

class logistik_rab_lines(models.Model):
	_name = 'logistik.rab.lines'
	_description = 'RAB Lines'
	_rec_name = 'product_id'

	rab_id = fields.Many2one('logistik.rab', string='No. Perkiraan/RAB', required=False, ondelete='cascade')
	# product_id = fields.Many2one('product.product', 'Kode Barang', required=True)
	product_id = fields.Many2one('product.template', 'Kode Barang', required=True)
	spesifikasi = fields.Text(string='Spesifikasi', related='product_id.description', readonly=True)
	pabrikan = fields.Char(string='Pabrikan', related='product_id.pabrikan', type='char', readonly=True)
	unit_id = fields.Many2one(string='Satuan Gudang', related='product_id.uom_id', readonly=True)
	kuantum = fields.Float('Pemakaian', digits=(11, 2), required=True)
	type = fields.Selection(related='product_id.pengadaan', selection=[
		('direksi', 'Direksi'),
		('lokal', 'Pabrik')
	], string='Pengadaan Oleh')
	harga = fields.Float('Harga', digits=(11, 2), required=True)
	sub_total = fields.Float(compute='_compute_sub_total', string='Sub Total', readonly=True)
	company_id = fields.Many2one(string='Unit/PG', related='rab_id.company_id', store=True, readonly=True)
	stasiun_id = fields.Many2one(string='Stasiun', related='rab_id.stasiun_id', store=True, readonly=True)

	_sql_constraints = [
		('product_unique', 'unique(rab_id, product_id)', 'Kode barang sudah tidak boleh dobel!')
	]

	@api.onchange('product_id')
	def onchange_product(self):
		self.kuantum = 0
		self.harga = 0

	@api.depends('kuantum', 'harga')
	def _compute_sub_total(self):
		for s in self:
			s.sub_total = s.kuantum * s.harga