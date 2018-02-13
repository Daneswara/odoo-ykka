from odoo import models, fields, api, exceptions

class logistik_spm_penggolongan_lines(models.TransientModel):
	_name = 'logistik.spm.penggolongan.lines'
	_description = "Wizard Detail Penggolongan"


	spm_line_id = fields.Many2one('logistik.spm.lines', string='SPM Line')
	repeat_order_id = fields.Many2one('purchase.order', string='Repeat SP')
	price_unit = fields.Float(string='Harga', digits=(16, 2), required=False, readonly=False)
	partner_id = fields.Many2one('res.partner', string='Rekanan', readonly=False)
	golongan_id = fields.Many2one('logistik.spm.penggolongan', string='Penggolongan', required=False)
	spm_id = fields.Many2one('logistik.spm', string='Nomor SPM', required=False)
	product_id = fields.Many2one('product.product', string='Kode Barang', required=False)
	product_description = fields.Text('Spesifikasi Barang', required=False)
	pkrat_id = fields.Many2one('logistik.pkrat', string='No. Investasi', required=False)
	unit_id = fields.Many2one('product.uom', string='Satuan', required=False)
	kuantum = fields.Float(string='Kuantum', digits=(11, 2), required=False)
	tgl_minta = fields.Date(string='Tgl. Serah', help='Tanggal Penyerahan yang diharapkan oleh user')

	@api.onchange('repeat_order_id')
	def action_onchange_repeat(self):
		self.price_unit = self.env['purchase.order.line'].search([('order_id', '=', self.repeat_order_id.id), ('product_id', '=', self.product_id.id)]).price_unit
		self.partner_id = self.repeat_order_id.partner_id.id
	
