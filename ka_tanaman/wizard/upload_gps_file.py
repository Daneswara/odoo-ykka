import base64
import random
import gpxpy
from odoo import models, fields
from odoo.exceptions import ValidationError

class gps_uploader(models.TransientModel):
	_name = 'gps.uploader.wizard'

	def proses_gps_to_text(self):
		ids = []
		dbarea = self.env['ka_plantation.area']
		gpx = gpxpy.parse(base64.decodestring(self.file_gps))
		for track in gpx.tracks:
			for segment in track.segments:
				coordinates = []
				for point in segment.points:	
					
					coordinates.append([point.latitude,point.longitude])

				coordinates.append(coordinates[0])
				string_coordinates = '%s'%coordinates
				# _dusun = track.name[0:5] #delete
				_kabupaten = track.name[0:1] if track.name else None
				_kecamatan = track.name[0:3] if track.name else None
				_desa = track.name[0:4] if track.name else None

				# sementara dimatikan dulu
				res_kabupaten = self.env['res.kab.kota'].search([('code', '=', _kabupaten)], limit=1)
				# if not _kabupaten or not res_kabupaten.id:
				# 	raise ValidationError("Tidak di temukan Kode Kabupaten %s" % _kabupaten)
					
				res_kecamatan = self.env['res.kecamatan'].search([('code', '=', _kecamatan)], limit=1)
				# if not _kecamatan or not res_kecamatan.id:
				# 	raise ValidationError("Tidak di temukan Kode Kecamatan %s" % _kecamatan)
					
				res_desa = self.env['res.desa.kelurahan'].search([('code', '=', _desa)], limit=1)
				# if not _desa or not res_desa.id:
				# 	raise ValidationError("Tidak di temukan Kode Desa %s" % _desa)
				
				# res_dusun = self.env['res.dusun'].search([('code', '=', _dusun)], limit=1)
				# if not _dusun or not res_dusun.id:
				# 	raise ValidationError("Tidak di temukan Kode Dusun %s" % _dusun)

				# area = self.env['ka_plantation.area'].search([('code', '=', track.name)], limit=1)
				# if area:
				# 	raise ValidationError("Data petak/area sudah ada! Upload data area yang lain.")

				vals = {
					'code_urut':track.name[4:] if track.name else None,
					'provinsi_id': res_kabupaten.provinsi_id.id if res_kabupaten.provinsi_id.id else None,
					'kabupaten_id': res_kabupaten.id if res_kabupaten.id else None,
					'kecamatan_id': res_kecamatan.id if res_kecamatan.id else None,
					'desa_id': res_desa.id if res_desa.id else None,
					'gps_polygon': string_coordinates if string_coordinates else None,
				}
				new_rec = dbarea.create(vals)
				ids.append(new_rec.id)

		return {
				'name':'Data Ter-Upload',
				'view_type': 'form',
				'view_mode': 'tree,form,areamap',
				'res_model': 'ka_plantation.area',
				'type': 'ir.actions.act_window',
				'domain': [('id', 'in', ids)],
				}

	file_gps = fields.Binary(string="Nama File",required=True)
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)