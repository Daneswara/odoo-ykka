import time
import ast
import geocoder
from shapely.geometry import Polygon, asShape
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
WGS84_RADIUS = 6378137
import matplotlib
matplotlib.use('pdf')
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import geojson
import numpy as np
from descartes import PolygonPatch
import os
import random
import pprint


class Area(models.Model):
	_name = 'ka_plantation.area'
	_description = "Lahan Kebun"
	_order = 'code'
	_rec_name = 'code'


	# code = fields.Char(string="Kode Lahan", size=9, required=True, readonly=True)
	code = fields.Char(string="Kode Petak", size=8, readonly=True)
	# code_urut = fields.Char(string="Kode Urutan", size=3, required=True)
	code_urut = fields.Char(string="Kode Urutan", size=4)
	owner = fields.Char(string="Pemilik")
	
	# dusun_id = fields.Many2one('res.dusun', string="Dusun", required=True)
	desa_id = fields.Many2one('res.desa.kelurahan', string="Desa / Kelurahan")
	kecamatan_id = fields.Many2one(related='desa_id.kecamatan_id', string="Kecamatan", readonly=True, store=True)
	kabupaten_id = fields.Many2one(related='kecamatan_id.kab_kota_id', string="Kabupaten", readonly=True, store=True)
	provinsi_id = fields.Many2one(related='kabupaten_id.provinsi_id', string="Provinsi", readonly=True, store=True)
	
	luas = fields.Float(string="Luas Lahan",compute='_compute_luas',store=True,digits=(5,3))
	gps_polygon = fields.Text(string="Data GPS")
	gps_mirror = fields.Text(string="Mirror Data GPS")
	status_contract = fields.Boolean(string="Status Kontrak", default=False)
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
	status_polygon = fields.Selection([
		('draft', 'DRAFT'),
		('valid', 'VALID'),
	], string="Status Polygon", default='draft', required=True)
	
	compute_map_address = fields.Text(string="Map Address", compute='_compute_map_address')
	postal = fields.Char(string="Kode Pos",store=True)

	#status False = belum valid/belum di validasi
	desa_name = fields.Char(string="Nama Desa", related='desa_id.name')
	kecamatan_name = fields.Char(string="Nama Kecamatan", related='kecamatan_id.name')
	kabupaten_name = fields.Char(string="Nama Kabupaten", related='kabupaten_id.name')
	tgl_upload = fields.Datetime(string="Tanggal Upload",required=False, readonly=False, default=lambda self: fields.datetime.now())
	tgl_validasi = fields.Datetime(string="Tanggal Validasi")
	upload_by = fields.Many2one('res.users', string="Upload oleh", default= lambda self: self.env.user.id)
	validate_by = fields.Many2one('res.users', string="Validate oleh")
	rehabilitation_ids = fields.One2many('ka_plantation.area.rehabilitation', 'area_id', string='Data Rahabilitasi')
	area_intersect_id = fields.Many2one('ka_plantation.area', string="Lahan Intersect")
	rehabilitation_ok = fields.Boolean(compute='_rehabilitation_ok', string='Sudah Rehabilitasi', store=True)

	farmer_id = fields.Many2one('ka_plantation.farmer', compute='_compute_last_farmer', string="No. Induk Petani")
	register_line_ids = fields.One2many('ka_plantation.register.line', 'area_id')
	register_count = fields.Integer(compute='_compute_register')
	taks_maret = fields.Float(string="Taks. Maret")
	# _sql_constraints = [
	# 	('area_code_company_unique', 'UNIQUE(code, company_id)', 'Dalam satu Unit/PG kode area/lahan tidak boleh sama!')
	# ]

	def open_register(self):
		registers = [reg.register_id.id for reg in self.register_line_ids]
		registers = list(set(registers))
		action = self.env.ref('ka_tanaman.action_register_readonly')
		result = action.read()[0]
		result['domain'] = [('id', 'in', registers)]
		return result

	@api.multi
	def _compute_register(self):
		for s in self:
			sql = """SELECT COUNT(register_id)
				FROM ka_plantation_register_line
				WHERE area_id=%s
				LIMIT 1""" %(str(s.id),)

			s._cr.execute(sql)
			fetch = s._cr.fetchall()
			for c_register_id, in fetch:
				s.register_count = int(c_register_id)
				break

	@api.multi
	def _compute_last_farmer(self):
		for s in self:
			sql = """SELECT a.id, b.id, b.farmer_id
				FROM ka_plantation_register_line a
				INNER JOIN ka_plantation_register b
				ON a.register_id=b.id
				WHERE a.area_id=%s
				ORDER BY a.id DESC
				LIMIT 1""" %(str(s.id),)

			s._cr.execute(sql)
			fetch = s._cr.fetchall()

			for line_id, register_id, farmer_id in fetch:
				s.farmer_id = farmer_id
				break

	@api.multi
	@api.depends('rehabilitation_ids')
	def _rehabilitation_ok(self):
		for this in self:
			this.rehabilitation_ok = (len(this.rehabilitation_ids) > 0)
	
	@api.multi
	@api.depends('gps_polygon')
	def _compute_map_address(self):
		for s in self:
			if not s.gps_polygon:
				s.compute_map_address = None
				return

			gps_list = ast.literal_eval(s.gps_polygon)
			lat_list = [g[0] for g in gps_list]
			lat_center = (lat_list[0] + lat_list[len(lat_list)-1]) / 2 
			lng_list = [g[1] for g in gps_list]
			lng_center = (lng_list[0] + lng_list[len(lng_list)-1]) / 2

			geo = geocoder.google([lat_center, lng_center], method='reverse')
			if not geo.address:
				s.compute_map_address = None
			s.compute_map_address = geo.address
			s.write({'postal':geo.postal})

	def _set_code(self, desa, code_urut):
		desa = desa or ''
		code_urut = code_urut or ''
		return desa + code_urut

	@api.model
	def create(self, vals):
		# _dusun = (self.env['res.dusun'].browse(vals['dusun_id']))
		_desa = (self.env['res.desa.kelurahan'].browse(vals['desa_id']))
		_kecamatan = _desa.kecamatan_id
		_kabupaten = _kecamatan.kab_kota_id
		_provinsi = _kabupaten.provinsi_id
		
		vals.update({
			'code': self._set_code(_desa.code, vals['code_urut']),
			# 'desa_id': _desa.id,
			'kecamatan_id': _kecamatan.id,
			'kabupaten_id': _kabupaten.id,
			'provinsi_id': _provinsi.id
		})
		
		if vals.has_key('gps_polygon'):
			if vals['gps_polygon']:
				vals.update({'gps_mirror': vals['gps_polygon']})
		if vals.has_key('gps_mirror'):
			if vals['gps_mirror']:
				vals.update({'gps_polygon': vals['gps_mirror']})
		return super(Area, self).create(vals)

	@api.multi
	def write(self, vals):
		_desa = (self.env['res.desa.kelurahan'].browse(vals['desa_id'])) if vals.has_key('desa_id') else self.desa_id
		_code_urut = vals['code_urut'] if vals.has_key('code_urut') else self.code_urut
		_kecamatan = _desa.kecamatan_id
		_kabupaten = _kecamatan.kab_kota_id
		_provinsi = _kabupaten.provinsi_id

		vals.update({
			'code': self._set_code(_desa.code, _code_urut),
			'kecamatan_id': _kecamatan.id,
			'kabupaten_id': _kabupaten.id,
			'provinsi_id': _provinsi.id
		})

		if vals.has_key('gps_mirror'):
			if vals['gps_mirror']:
				vals.update({'gps_polygon': vals['gps_mirror']})
		return super(Area, self).write(vals)

	@api.multi
	def unlink(self):
		for s in self:
			if s.status_polygon == 'valid':
				raise ValidationError('Tidak dapat menghapus data valid.')
		
		return super(Area, self).unlink()

	@api.onchange('code')
	def onchange_code(self):
		self.kabupaten_id = None
		self.kecamatan_id = None
		self.desa_id = None
		if not self.code:
			return
		_kabupaten = self.code[0:1]
		self.kabupaten_id = self.env['res.kab.kota'].search([('code', '=', _kabupaten), ('company_id', '=', self.company_id.id)], limit=1).id
		_kecamatan = self.code[1:2]
		self.kecamatan_id = self.env['res.kecamatan'].search([('code', '=', _kecamatan), ('company_id', '=', self.company_id.id)], limit=1).id
		_desa = self.code[2:3]
		self.desa_id = self.env['res.desa.kelurahan'].search([('code', '=', _desa), ('company_id', '=', self.company_id.id)], limit=1).id

	# # @override
	# @api.multi
	# def name_get(self):
	# 	res = []
	# 	for s in self:
	# 		code = s.code or ''
	# 		owner = s.owner or ''
	# 		res.append((s.id, code + ' - ' + owner))

	# 	return res

	# # @override
	# @api.model
	# def name_search(self, name='', args=None, operator='ilike', limit=80):
	# 	if not args:
	# 		args = []

	# 	if name:
	# 		record = self.search([('code', operator, name)] + args, limit=limit)
	# 		if not record:
	# 			record = self.search([('name', operator, name)] + args, limit=limit)
	# 	else:
	# 		record = self.search(args, limit=limit)

	# 	return record.name_get()

	@api.onchange('desa_id', 'code_urut')
	def onchange_code(self):
		_desa = self.desa_id.code if self.desa_id else ''
		_code_urut = self.code_urut if self.code_urut else ''
		self.code = self._set_code(_desa, _code_urut)

	@api.one
	def set_contract(self, status):
		return self.write({'status_contract': status})

	@api.multi
	@api.depends('gps_polygon')
	def _compute_luas(self):
		for s in self:
			data_gps_polygon = s.gps_polygon
			if data_gps_polygon:
				temp_split = data_gps_polygon.replace('[','').split('],')
				list_data_gps = [map(float, ts.replace(']','').split(',')) for ts in temp_split]
				coordinates = np.array(list_data_gps)
				poly = Polygon(np.radians(coordinates))
				hasil_WGS = poly.area*WGS84_RADIUS**2
				luas_area_hektar = hasil_WGS / 10000
				s.luas = luas_area_hektar

	def validasi_intersect(self):
		data_gps = self.gps_polygon
		id_intersect = None
		if data_gps:
			split_data_gps = data_gps.replace('[','').split('],')
			list_data_gps = [map(float, s.replace(']','').split(',')) for s in split_data_gps]
			polygon1 = Polygon(list_data_gps)
			polygon2 = self.search([('status_polygon', '=' , 'valid'),('id','!=',self.id),('desa_id','=',self.desa_id.id)],order='id desc')
			if not polygon2:
				self.status_polygon = 'valid'
				
			i = 1
			for s in polygon2:
				if s.gps_polygon:
					split_data_gps2 = s.gps_polygon.replace('[','').split('],')
					list_data_gps2 = [map(float, k.replace(']','').split(',')) for k in split_data_gps2]
					data_polygon2 = Polygon(list_data_gps2)
					cek_intersects = polygon1.intersects(data_polygon2)
					if cek_intersects == True:
						self.area_intersect_id = s.id
						return False
						# break
					else:
						if i == len(polygon2):
							self.status_polygon = 'valid'
							self.tgl_validasi  =  fields.Datetime.now()
							# self.write({'status_polygon':True})
							return True
				i+=1
		else:
			raise ValidationError("Data GPX tidak boleh Kosong!!")


	@api.multi
	def action_valid(self):
		is_valid = True

		if not self.code_urut:
			raise ValidationError("Kode petak/lahan tidak boleh kosong")

		area = self.env['ka_plantation.area'].search([('code', '=', self.code)])
		if len(area) > 1:
			raise ValidationError("Kode petak/lahan sudah ada! Ganti kode yang lain.")
		
		_kabupaten = self.code[:1]
		_kecamatan = self.code[1:2]
		_desa = self.code[2:3]
		_code_urut = self.code[3:]
	
		if not self.kabupaten_id:
			res_kabupaten = self.env['res.kab.kota'].search([('code', '=', _kabupaten)], limit=1)
			if not _kabupaten or not res_kabupaten.id:
				raise ValidationError("Tidak di temukan Kode Kabupaten %s" % _kabupaten)
			
			self.kabupaten_id = res_kabupaten.id
			
		if not self.kecamatan_id:		
			res_kecamatan = self.env['res.kecamatan'].search([('code', '=', _kecamatan)], limit=1)
			if not _kecamatan or not res_kecamatan.id:
				raise ValidationError("Tidak di temukan Kode Kecamatan %s" % _kecamatan)

			self.kecamatan_id = res_kecamatan.id

		if not self.desa_id:
			res_desa = self.env['res.desa.kelurahan'].search([('code', '=', _desa)], limit=1)
			if not _desa or not res_desa.id:
				raise ValidationError("Tidak di temukan Kode Desa %s" % _desa)

			self.desa_id = res_desa.id

		if self.validasi_intersect():
			if self.area_intersect_id:
				self.area_intersect_id = None
				self._cr.commit()

			return {
				'type': 'ir.actions.act_window',
				'name': 'Form Area Lahan Kebun',
				'res_model': self._name,
				'view_type' : 'form',
				'view_mode' : 'form',
				'res_id': self.id,
			}
		else:
			return self.call_intersect_wizard()

	@api.multi
	def action_draft(self):
		self.write({'status_polygon': 'draft'})
		return {
			'type': 'ir.actions.act_window',
			'name': 'Form Area Lahan Kebun',
			'res_model': self._name,
			'view_type' : 'form',
			'view_mode' : 'form',
			'res_id': self.id,
		}

	@api.multi
	@api.depends('status_polygon')
	def _compute_status(self):
		for s in self:
			cek_valid = s.status_polygon
			if cek_valid == True:
				s.status_validasi = "VALID"
			else:
				s.status_validasi = "DRAFT"



	@api.multi
	def call_intersect_wizard(self):
		view_id = self.env['ka_plantation.area.intersect']
		kode_intersect = self.env['ka_plantation.area'].search([('id', '=', self.area_intersect_id.id)], limit=1).code		
		pemilik_intersect = self.env['ka_plantation.area'].search([('id', '=', self.area_intersect_id.id)], limit=1).owner		
		
		if not pemilik_intersect:
			pemilik_intersect = "Belum di ketahui."

		vals = {
				'name'   : "Intersection dengan kode lahan: " + kode_intersect + " - milik: " + pemilik_intersect,
			}
		new = view_id.create(vals)
		return {
			'type': 'ir.actions.act_window',
			'name': 'Intersect Wizard',
			'res_model': 'ka_plantation.area.intersect',
			'res_id' : new.id,
			'view_type': 'form',
			'view_mode': 'form',
			'target': 'new'
		}

	def export_to_gpx(self):
		return {
			'type': 'ir.actions.act_url',
			'url': '/web/ka_plantation/area/download?id=%s'%(self.id),
			'target': 'current'
		}

	def action_rehabilitation(self):
		action = self.env.ref('ka_tanaman.action_area_rehabilitation')
		result = action.read()[0]
		result['domain'] = [('area_id', '=', self.id)]
		result['context'] = {
			'default_area_id' : self.id
		}
		return result

	def cetak_polygon(self,kategori,kategori_id,kategori_name):
		batas_desa = []
		path_jalan =''
		path_sungai = ''
		path_area = ''
		if kategori == 'desa':
			data = geojson.loads(geojson.dumps(self.search([('desa_id','=',kategori_id)]).get_geojson()))
			batas = self.env['res.desa.kelurahan'].search([('id','=',kategori_id)])
			batas_desa.append(batas.code)
		if kategori == 'kecamatan':
			data = geojson.loads(geojson.dumps(self.search([('kecamatan_id','=',kategori_id)]).get_geojson()))
			batas = self.env['res.kecamatan'].search([('id','=',kategori_id)]).desa_ids
			for desa_id in batas:
					batas_desa.append(desa_id.code)
		if kategori == 'kabupaten':
			data = geojson.loads(geojson.dumps(self.search([('kabupaten_id','=',kategori_id)]).get_geojson()))
			batas = self.env['res.kab.kota'].search([('id','=',kategori_id)]).kecamatan_ids
			for kec_id in batas:
				for desa_id in kec_id.desa_ids:
					batas_desa.append(desa_id.code)
		
		fig,ax = plt.subplots(figsize=(46.81,33.11))
		max_lat = []
		max_long = []
		min_lat = []
		min_long = []
		for feat in data["features"]:
			#conver lat long to projection unit
			coordlist = feat['geometry']['coordinates'][0]
			long_batas,lat_batas = zip(*coordlist)
			max_lat.append(max(lat_batas))
			max_long.append(max(long_batas))
			min_lat.append(min(lat_batas))
			min_long.append(min(long_batas))

		lat_0 = (max(max_lat)+min(min_lat))/2
		long_0 = (max(max_long)+min(min_long))/2



		m = Basemap(projection='lcc', llcrnrlon=min(min_long), llcrnrlat=min(min_lat), urcrnrlon=max(max_long), 
			urcrnrlat=max(max_lat), lat_0=lat_0, lon_0=long_0, resolution='h', ax=ax)
		# m = Basemap(projection='lcc', llcrnrlon=111.0679652, llcrnrlat=-6.6555482, urcrnrlon=111.0834147, 
		# 	urcrnrlat=-6.6310802, lat_0=-6.4913484, lon_0=111.123949, resolution='h', ax=ax)


		m.drawcoastlines()
		m.drawstates()
		m.drawcountries()

		dirname = os.path.dirname(os.path.realpath(__file__))
		static_path = os.path.realpath(dirname + '/../static/')

		m.readshapefile(static_path + '/src/shp/JALAN_LN', 'jalan', color='gray')
		m.readshapefile(static_path + '/src/shp/SUNGAI_LN', 'sungai', color='lightgreen')
		m.readshapefile(static_path + '/src/shp/DESA_AR', 'desa', linewidth=1, color='r',  drawbounds = True)

		# for info, shape in zip(m.desa_info, m.desa):
		# 	for i in batas_desa:
		# 		if info['KDPPUM'] == i:
		# 			x, y = zip(*shape) 
		# 			m.plot(x, y, 'r--', marker='+')
		# 			print x,y
		# 		else:
		# 			print "elseee"

		# for info, shape in zip(m.jalan_info, m.jalan):
		# 	if info['NAMRJL'] == 'Jalan Arteri':
		# 		x, y = zip(*shape) 
		# 		m.plot(x, y, marker='3',color='b')

		centroid = []
		for feat in data["features"]:
			#conver lat long to projection unit
			coordlist = feat['geometry']['coordinates'][0]
			for j in range(len(coordlist)):
				coordlist[j][0],coordlist[j][1]=m(coordlist[j][0],coordlist[j][1])
			poly = {"type":"Polygon","coordinates":[coordlist]}
			# convert the geometry to shapely
			geom = asShape(poly)
			# obtain the coordinates of the feature's centroid
			cx, cy = geom.centroid.x, geom.centroid.y    
			# label the features at the centroid location
			ax.text(cx,cy, feat['properties']['kode_petak'], fontsize=6, bbox = dict(fc='w', alpha=0.3))
			if feat['properties']['states'] == 'valid':
				if feat['properties']['rehabilitation_ok'] == True:
					patch_poly = PolygonPatch(poly, hatch='..', color='green', ec='green', lw=0.5,fill=False)
				else:
					patch_poly = PolygonPatch(poly, hatch='..', color='blue', ec='blue', lw=0.5,fill=False)
			if feat['properties']['states'] == 'draft':
				if feat['properties']['rehabilitation_ok'] == True:
					patch_poly = PolygonPatch(poly, hatch='..', color='orange', ec='orange', lw=0.5,fill=False)
				else:
					patch_poly = PolygonPatch(poly, hatch='..', color='red', ec='red', lw=0.5,fill=False)
			ax.add_patch(patch_poly)

		#adjust figurr margin
		# plt.tight_layout(pad=5)
		#add legend
		low = mpatches.Patch(color='green', linewidth=0.5, linestyle='-', label='Sungai')
		med = mpatches.Patch(color='black', linewidth=0.5, linestyle='-', label='Jalan')
		high = mpatches.Patch(color='red', linewidth=0.5, linestyle='-', label='Desa')
		plt.legend(handles=[low,med,high], title='Legend')    

		# #Add Title
		plt.title("PETAK " + kategori.upper() + " " +kategori_name)
		name_list = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890~!@#$%^&*()'
		rand = ''
		for i in range(12):
			idx = random.randint(0, len(name_list) - 1)
			rand += name_list[idx]
		plt.savefig('/var/lib/odoo/test_' + rand + '.pdf', dpi=150)
		read_pdf = open("/var/lib/odoo/test_" + rand + ".pdf", "r")
		file_attachment = read_pdf.read()
		os.unlink('/var/lib/odoo/test_' + rand + '.pdf')
		return file_attachment

	@api.multi
	def get_geojson(self):
		area_json = []
		for this in self:
			data_gps = this.gps_polygon
			if data_gps:
				split_data_gps = data_gps.replace('[','').split('],')
				list_data_gps = [map(float, s.replace(']','').split(',')) for s in split_data_gps]
				list_data_json = []
				for i in list_data_gps:
					if i[0] < i[1]:
						list_data_json.append([i[1],i[0]])
					else:
						list_data_json.append([i[0],i[1]])
				petak_json = {
						"type": "Feature",
						"properties": {
							"states": this.status_polygon,
							"desa_name" : this.desa_id.name,
							"kode_petak" : this.code,
							"rehabilitation_ok" : this.rehabilitation_ok
						},
						"geometry": {
						"type": "Polygon",
						"coordinates": [list_data_json]
						}
					}
				area_json.append(petak_json)
		data_json = {
			"type": "FeatureCollection",
			"features": area_json
			}
		return data_json



class AreaAgronomi(models.Model):
	_name = 'ka_plantation.area.agronomi'

	area_id = fields.Many2one('ka_plantation.area', string="Kode Petak")
	intensifikasi_id = fields.Many2one('ka_plantation.intensifikasi', string="Intensifikasi",store=True)
	varietas_id = fields.Many2one('ka_plantation.varietas', string="Varietas")
	tebang_periode_id = fields.Many2one('ka_plantation.periode', string="Masa Tebang")
	tanam_periode_id = fields.Many2one('ka_plantation.periode', string="Masa Tanam")
	luas = fields.Float(related='area_id.luas', digits=(5,3), string="Luas", store=True)
	desa_id = fields.Many2one(related='area_id.desa_id', string="Desa",readonly=True,store=True)
	kecamatan_id = fields.Many2one(related='area_id.kecamatan_id', string="Kecamatan",store=True)
	kabupaten_id = fields.Many2one(related='area_id.kabupaten_id', string="Kabupaten")
	mtt_id = fields.Many2one('ka_plantation.mtt',string="MTT")
	session = fields.Many2one(related='mtt_id.session_id', string="Masa Giling",readonly=True)
	company_id = fields.Many2one(string="Unit/PG",related="area_id.company_id",readonly=True,store=True)
	taks_produksi = fields.Float(string="Taks. Produksi")
	register_type = fields.Selection([
		('ts', "TS"),
		('trk', "TRK"),
		('trm', "TRM"),
	],string="Type", default='trm')


	@api.one
	@api.constrains('area_id','mtt_id')
	def _constraint_area_mtt(self):
		if len(self.search([('area_id', '=', self.area_id.id),('mtt_id','=',self.mtt_id.id)])) > 1:
			raise ValidationError("Nomor Petak sudah terdaftar atas pada Register lain!")
			
	@api.multi
	def name_get(self):
		res = []
		for s in self:
			area = s.area_id.code or ''
			res.append((s.id,'Agronomi Petak ' + area))

		return res