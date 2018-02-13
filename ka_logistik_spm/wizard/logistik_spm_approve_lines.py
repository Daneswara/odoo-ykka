from odoo import models, fields

class logistik_spm_approve_lines(models.TransientModel):
	_name = 'logistik.spm.approve.lines'
	_description = 'Wizard Detail Partial Picking'
	
	wizard_id = fields.Many2one('logistik.spm.approve', string='Nomor SPM', readonly=True, ondelete='cascade')
	spm_line_id = fields.Many2one('logistik.spm.lines', string='SPM Item', readonly=True)
	product_id = fields.Many2one('product.template', string='Kode Barang', required=True, readonly=True)
	product_desc = fields.Text(string='Spesifikasi Barang', related='product_id.description', readonly=True)
	# product_id = fields.Many2one('product.product', string='Kode Barang', required=True, readonly=True)
	unit_id =  fields.Many2one(string='Satuan', related='product_id.uom_id', readonly=True)
	spesifikasi = fields.Text(string='Spesifikasi Yang Diminta', related='spm_line_id.spesifikasi', readonly=True)
	kuantum = fields.Float(string='Qty Setuju', digits=(11, 2), required=True, readonly=True)
	qty_partial = fields.Float(string='Realisasi', digits=(11, 2), required=True)
	tgl_minta =  fields.Date(string='Tgl. Diminta', help='Tanggal Penyerahan yang diharapkan oleh user', required=True)
	pkrat_id = fields.Many2one('logistik.pkrat', string='No. Investasi')