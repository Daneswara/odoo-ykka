from odoo import models, fields, api
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import base64
import tempfile
from odoo.exceptions import ValidationError
import os
from shapely.geometry import Point,Polygon

class AreaRehabilitation(models.Model):
	_name = 'ka_plantation.area.rehabilitation'
	_description = "Rehabilitasi Petak Lahan"
	_inherit = ['mail.thread']

	area_id = fields.Many2one('ka_plantation.area', string="Register Petak", required=True)
	luas = fields.Float(related='area_id.luas', string='Luas(Ha)', readonly=True)
	desa_id = fields.Many2one(related='area_id.desa_id', string='Desa', store=True, readonly=True)
	zona_id = fields.Many2one('ka_plantation.zona.rate', string='Zona')
	kecamatan_id = fields.Many2one(related='desa_id.kecamatan_id', string="Kecamatan", readonly=True, store=True)
	kabupaten_id = fields.Many2one(related='kecamatan_id.kab_kota_id', string="Kabupaten", readonly=True, store=True)
	date_delivery = fields.Date(string="Tanggal", required=True)
	farmer_name = fields.Char(string="Nama Petani", required=True)
	plpg_name = fields.Char(string="PLPG", required=True)
	area_type = fields.Selection([
		('ts', "TS"),
		('tr', "TR"),
	],string="Jenis TS/TR", required=True)
	rehabilitation_type = fields.Selection([
		('kompos', 'Kompos'),
		('blotong', 'Blotong')
	], string="Jenis Rehabilitasi", required=True)
	quantity = fields.Float(string="Jumlah (Ton)", required=True)
	geo_photo = fields.Binary(string="Photo")
	geo_ok = fields.Boolean(default=False)
	state = fields.Selection([
		('draft','Draft'),
		('valid', 'Validate')
	],default='draft',track_visibility='onchange')
	latitude = fields.Float(digits=(6,12))
	longitude = fields.Float(digits=(6,12))
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
	rit = fields.Integer(string="Rit")
	tarif = fields.Float(string="Tarif Zona")
	biaya = fields.Float(string="Jumlah Biaya")
	
	@api.multi
	def name_get(self):
		res = []
		for s in self:
			area = s.area_id.code or ''
			res.append((s.id, 'Rehabilitasi Lahan ' + area))

		return res

	# def action_valid(self):
	# 	koordinat_photo = Point(self.latitude, self.longitude)
	# 	split_data_gps = self.area_id.gps_polygon.replace('[','').split('],')
	# 	list_data_gps = [map(float, s.replace(']','').split(',')) for s in split_data_gps]
	# 	polygon = Polygon(list_data_gps)
	# 	if polygon.contains(koordinat_photo):
	# 		self.geo_ok = True
	# 		self.state = 'valid'
	# 	else:
	# 		raise ValidationError('Koordinat foto tidak cocok!')

	def action_draft(self):
		self.state = 'draft'

	def action_valid(self):
		self.state = 'valid'
	
	@api.onchange('area_id')
	def onchange_area_id(self):
		if self.area_id.owner:
			self.farmer_name = self.area_id.owner
	
	@api.onchange('geo_photo')
	def _onchange_geo_photo(self):
		if self.geo_photo:
			data = base64.decodestring(self.geo_photo)
			fobj = tempfile.NamedTemporaryFile(delete=False)
			fname = fobj.name
			fobj.write(data)
			fobj.close()
			try:
				exif_data = self.get_exif(fname)
				if exif_data.has_key('Datetime') and exif_data['Datetime']:
					self.date_delivery = exif_data['DateTime'].replace(':','-')
				lat_lon = self.get_lat_lon(exif_data)
				self.latitude = lat_lon[0]
				self.longitude = lat_lon[1]
			except Exception as e:
				print "---------------ini error dari exception---------------"
				print e
				return {
					'warning': {
						'title': "Images Error",
						'message': "Data foto kurang lengkap!",
					},
					# 'value': {
						# 'geo_photo': None
					# }
				} 
			finally:
				os.unlink(fname)

	def get_exif(self,filename):
		exif_data = {}
		i = Image.open(filename)
		info = i._getexif()
		for tag, value in info.items():
			decoded = TAGS.get(tag, tag)
			if decoded == "GPSInfo":
				gps_data = {}
				for t in value:
					sub_decoded = GPSTAGS.get(t, t)
					gps_data[sub_decoded] = value[t]
				exif_data[decoded] = gps_data
			else:
				exif_data[decoded] = value
		return exif_data

	def _get_if_exist(self,data, key):
		if key in data:
			return data[key]

		return None

	def _convert_to_degress(self,value):
		"""Helper function to convert the GPS coordinates stored in the EXIF to degress in float format"""
		d0 = value[0][0]
		d1 = value[0][1]
		d = float(d0) / float(d1)

		m0 = value[1][0]
		m1 = value[1][1]
		m = float(m0) / float(m1)

		s0 = value[2][0]
		s1 = value[2][1]
		s = float(s0) / float(s1)

		return d + (m / 60.0) + (s / 3600.0)

	def get_lat_lon(self,exif_data):
		"""Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)"""
		lat = None
		lon = None

		if "GPSInfo" in exif_data:		
			gps_info = exif_data["GPSInfo"]

			gps_latitude = self._get_if_exist(gps_info, "GPSLatitude")
			gps_latitude_ref = self._get_if_exist(gps_info, 'GPSLatitudeRef')
			gps_longitude = self._get_if_exist(gps_info, 'GPSLongitude')
			gps_longitude_ref = self._get_if_exist(gps_info, 'GPSLongitudeRef')

			if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
				lat = self._convert_to_degress(gps_latitude)
				if gps_latitude_ref != "N":                     
					lat = 0 - lat

				lon = self._convert_to_degress(gps_longitude)
				if gps_longitude_ref != "E":
					lon = 0 - lon

		return lat, lon

	@api.onchange('desa_id')
	def onchange_desa_id(self):
		self.zona_id = self.env['ka_plantation.zona.rate'].search([('desa_ids','=',self.desa_id.id)]).id
		
	@api.onchange('zona_id','rit')
	def onchange_zona_rit(self):
		# this.tarif = self.env['ka_plantation.zona.rate'].search([('desa_ids','=',this.desa_id.id)]).tarif
		self.tarif = self.zona_id.tarif
		self.biaya = self.rit * self.tarif