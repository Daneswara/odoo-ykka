from odoo import models, fields, api

class logistik_pkrat_fisik(models.Model):
	_name = 'logistik.pkrat.fisik'
	_description = "PKRAT Kontrak"
	
	pkrat_id = fields.Many2one('logistik.pkrat', string='Nama Proyek')
	nomor = fields.Char(string='Nomor Berita Acara', size=15, required=True)
	tanggal = fields.Date(string='Tanggal', required=True)
	progress = fields.Float(string='Prosentase Kemajuan (%)', digits=(5, 2), required=True)
	keterangan = fields.Char(string='Keterangan', size=128)
	nilai = fields.Float(string='Nilai Pembayaran', digits=(5, 2), required=True)