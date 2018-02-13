# ----------------------------------------------------------
# Data base wilayah Indonesia
# res.provinsi = Data Provinsi
# res.kab.kota = Data Kabupaten dan Kota
# res.kecamatan = Data Kecamatan
# res.desa.kelurahan = Data Desa dan Kelurahan
# ----------------------------------------------------------

from odoo import models, fields, api

class res_provinsi(models.Model):
	_name = 'res.provinsi'

	code = fields.Char(string="Kode", size=5, required=True)
	name = fields.Char(string="Nama Provinsi", required=True, size=128)

class res_kab_kota(models.Model):
	_name = 'res.kab.kota'

	code = fields.Char(string="Kode", size=5, required=True)
	name = fields.Char(string="Nama Kabupaten / Kota", required=True, size=128)
	provinsi_id = fields.Many2one('res.provinsi', string="Provinsi", required=True)

class res_kecamatan(models.Model):
	_name = 'res.kecamatan'

	code = fields.Char(string="Kode", size=5, required=True)
	name = fields.Char(string="Nama Kecamatan", required=True, size=128)
	kab_kota_id = fields.Many2one('res.kab.kota', string="Kabupaten / Kota", required=True)
	provinsi_id = fields.Many2one(string="Provinsi", related='kab_kota_id.provinsi_id', readonly=True)

class res_desa_kelurahan(models.Model):
	_name = 'res.desa.kelurahan'

	code = fields.Char(string="Kode", size=5, required=True)
	name = fields.Char(string="Nama Desa / Kelurahan", required=True, size=128)
	kecamatan_id = fields.Many2one('res.kecamatan', string="Kecamatan", required=True)
	kab_kota_id = fields.Many2one(string="Kabupaten / Kota", related='kecamatan_id.kab_kota_id', readonly=True)
	provinsi_id = fields.Many2one(string="Provinsi", related='kab_kota_id.provinsi_id', readonly=True)

class res_dusun(models.Model):
	_name = 'res.dusun'

	code = fields.Char(string="Kode", size=5, required=True)
	nama = fields.Char(string="Dusun", required=True,size=128)
	desa_kelurahan_id = fields.Many2one('res.desa.kelurahan',string="Nama Dusun",required=True)
		