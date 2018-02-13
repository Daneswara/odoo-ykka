from odoo import models, fields
from odoo.exceptions import ValidationError


class AreaPrintPolygon(models.TransientModel):
	_name = 'ka_plantation.area.print.polygon'


	pilih_kategori = fields.Selection([
		('desa', 'Desa'),
		('kecamatan', 'Kecamatan'),
		('kabupaten', 'Kabupaten'),
	], string="Cetak Polygon Berdasarkan", default='desa', required=True)

	desa_id = fields.Many2one('res.desa.kelurahan', string="Desa / Kelurahan")
	kecamatan_id = fields.Many2one('res.kecamatan', string="Kecamatan")
	kab_kota_id = fields.Many2one('res.kab.kota', string="Kabupaten / Kota")
	
	def wizard_cetak_polygon(self):
		kategori_id = None
		name = ""
		if self.pilih_kategori == 'desa':
			kategori_id = self.desa_id.id
			data = self.env['ka_plantation.area'].search([('desa_id','=',kategori_id)]).get_geojson()
			name = "Desa " + self.desa_id.name
		if self.pilih_kategori == 'kecamatan':
			kategori_id = self.kecamatan_id.id
			data = self.env['ka_plantation.area'].search([('kecamatan_id','=',kategori_id)]).get_geojson()
			name = "Kecamatan " + self.kecamatan_id.name
		if self.pilih_kategori == 'kabupaten':
			kategori_id = self.kab_kota_id.id
			data = self.env['ka_plantation.area'].search([('kabupaten_id','=',kategori_id)]).get_geojson()
			name = "Kabupaten " + self.kab_kota_id.name

		if data['features']:
			return {
				'type': 'ir.actions.act_url',
				'url': '/web/ka_plantation/area/print_polygon?id=%s' % (self.id),
				'target': 'current'
			}
		else:
			raise ValidationError("Data petak dalam area " + name + " tidak ditemukan!!")