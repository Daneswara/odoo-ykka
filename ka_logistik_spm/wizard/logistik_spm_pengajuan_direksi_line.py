from odoo import models, fields

class logistik_spm_pengajuan_direksi_line(models.TransientModel):
	_name = 'logistik.spm.pengajuan.direksi.line'
	_description = "Wizard Detail Pengajuan SPM Direksi"
	
	rec_id = fields.Integer(string='Record ID')
	spm_id = fields.Many2one('logistik.spm.pengajuan.direksi', string='Nomor SPM')
	# product_id = fields.Many2one('product.product', string='Kode/Nama Barang')
	product_id = fields.Many2one('product.product', string='Kode/Nama Barang')
	spesifikasi = fields.Text(string='Spesifikasi Barang', required=False)
	kuantum = fields.Float(string='Jml Setuju', digits=(11, 2))
	tgl_minta = fields.Date(string='Tgl. Diminta')
	stasiun_id = fields.Many2one('account.analytic.stasiun', string='Stasiun')
	account_id = fields.Many2one('account.account', string='No. Perkiraan')
	pkrat_id = fields.Many2one('logistik.pkrat', string='No. Investasi')
	selected = fields.Boolean('Diproses', default=True)
	pengajuan_id = fields.Many2one('logistik.pengajuan.spm',string='No. SPM')