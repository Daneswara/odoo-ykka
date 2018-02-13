from odoo import models, fields, api
import itertools
from odoo.exceptions import ValidationError

class AreaSampling(models.Model):
	_name = 'ka_plantation.sampling'

	tanggal = fields.Date(string="Tanggal",default=lambda self: fields.datetime.now())
	jumlah_kebijakan = fields.Float(string="Jumlah (%) ",required=True)
	luas_sampling = fields.Float(string="Luas Sampling",digits=(3,2),store=True)#sampling (A)
	luas_sampling_kecamatan = fields.Float("Luas Plot Sampling / Kecamatan",digits=(3,2),store=True)#sampling (B)
	jumlah_int_var = fields.Integer(string="Jumlah Kombinasi",compute='_compute_jumlah_sampling',store=True)#sampling (C)
	luas_plot_sampling = fields.Float(string="Luas Plot Sampling",digits=(3,2))#sampling (C)
	rata_luas = fields.Float(string="Rata-rata Luas per petak",compute='_compute_jumlah_sampling',digits=(3,2),store=True)#sampling (D)
	jumlah_sampling = fields.Integer(string="Jumlah Petak Sampling",compute='_compute_jumlah_sampling',readonly=True,store=True)#sampling (D)
	mtt_id = fields.Many2one('ka_plantation.mtt',string="MTT")
	company_id = fields.Many2one('res.company', string='Company',readonly=True, required=True,default=lambda self: self.env['res.company']._company_default_get('ka_plantation.sampling.area'))
	line_ids = fields.One2many('ka_plantation.sampling.line','sampling_id')
	state = fields.Selection([
		('draft', 'DRAFT'),
		('valid', 'VALID'),
	], string="Status Validasi", default='draft', required=True)
	taks_periode = fields.Selection([
		('maret', 'Maret'),
		('desember', 'Desember'),
	], string="Periode Taksasi", default='maret', readonly=True)

	_mtt_temp = fields.Integer(string="Temp mtt",compute='_compute_temp_mtt')

	@api.multi
	def name_get(self):
		res = []
		for s in self:
			taun = s.mtt_id.name or ''
			res.append((s.id, 'Sampling MTT ' + taun))

		return res

	@api.multi
	@api.depends('mtt_id')
	def _compute_temp_mtt(self):
		self._mtt_temp = self.mtt_id.id

	def _get_count_intensifikasi(self):
		sql = """ SELECT 
						count(DISTINCT(a.intensifikasi_id))
					FROM 
						ka_plantation_area_agronomi a
					-- INNER JOIN 
					-- 	ka_plantation_register_line b ON a.id = b.register_id
					WHERE 
							a.intensifikasi_id IS NOT NULL 
						AND 
							a.company_id = %s;""" %(str(self.company_id.id))
		self._cr.execute(sql)
		return self._cr.fetchall()[0][0]

	def _get_count_varietas(self):
		sql = """ SELECT 
						count(DISTINCT(a.varietas_id))
					FROM 
						ka_plantation_area_agronomi a
					-- INNER JOIN 
					-- 	ka_plantation_register_line b ON a.id = b.register_id
					WHERE 
							a.varietas_id IS NOT NULL 
						AND 
							a.company_id = %s;""" %(str(self.company_id.id))
		self._cr.execute(sql)
		return self._cr.fetchall()[0][0]

	@api.depends('jumlah_kebijakan')
	def _compute_jumlah_sampling(self):
		if self.jumlah_kebijakan > 0: 
			# print "perhitungan luas sampling (A)"
			area = self.env['ka_plantation.area'].search([('status_polygon', '=', 'valid'),('company_id','=',self.company_id.id)])
			luas_area = sum([a.luas for a in area])
			self.luas_sampling = self.jumlah_kebijakan * luas_area

			# print "perhitungan luas sampling per kecamatan (B)"
			jum_kecamatan = self.env['res.kecamatan'].search_count([('company_id','=',self.company_id.id)])
			self.luas_sampling_kecamatan = self.luas_sampling / jum_kecamatan

			# print "perhitungan plot sampling (c)"
			# intensifikasi = (self.env['ka_plantation.register.line'].search([('intensifikasi_id','!=',False),('company_id','=',self.company_id.id)]).mapped('intensifikasi_id'))
			# varietas = (self.env['ka_plantation.register.line'].search([('varietas_id','!=',False),('company_id','=',self.company_id.id)]).mapped('varietas_id'))
			self.jumlah_int_var = self._get_count_varietas() * self._get_count_intensifikasi()
			print self.jumlah_int_var
			if self.jumlah_int_var > 0:
				self.luas_plot_sampling = self.luas_sampling_kecamatan / self.jumlah_int_var
			else:
				raise ValidationError('Data Intensifikasi / Varietas tidak lengkap!')

			# print "perhitungan jumlah sampling (d)"
			jumlah_petak = self.env['ka_plantation.area'].search_count([('status_polygon', '=', 'valid'),('company_id','=',self.company_id.id)])
			self.rata_luas= luas_area/jumlah_petak
			self.jumlah_sampling = round(self.luas_plot_sampling / self.rata_luas)


	@api.multi
	def action_create_line_ids(self):
		self._cr.execute("DELETE FROM ka_plantation_sampling_line WHERE sampling_id = %s;",(self.id,))
		self._cr.execute("""SELECT 
								d.id,
								COUNT(DISTINCT a.intensifikasi_id) AS jumlah_int, 
								count(DISTINCT a.varietas_id) AS jumlah_var, 
								SUM(DISTINCT c.luas) AS luas_petak, 
								count(DISTINCT(c.id)) AS jumlah_petak 
							FROM
								ka_plantation_area_agronomi a
							INNER JOIN 
								ka_plantation_area c ON a.area_id = c.id
							INNER JOIN 
								res_kecamatan d ON c.kecamatan_id = d.id
							WHERE
									a.mtt_id = %s
								AND 
									a.intensifikasi_id IS NOT NULL 
								AND 
									a.varietas_id IS NOT NULL 
								AND 
									c.status_polygon = 'valid'
								AND
									d.company_id = %s
							GROUP BY 
									d.id;""", (str(self._mtt_temp), str(self.company_id.id),))
									
		line_ids = self._cr.fetchall()
		for j in line_ids:
			data ={
				'sampling_id': self.id,
				'kecamatan_id' : j[0],
				'jumlah_intensifikasi' : int(j[1]),
				'jumlah_varietas': int(j[2]),
				'luas_petak' : j[3],
				'jumlah_petak' : int(j[4]),
				'jumlah_sampling' : self.jumlah_sampling
				}
			self.env['ka_plantation.sampling.line'].create(data)

		for s in self.line_ids:
			s.create_sampling_taksasi()
			s.create_sampling_kombinasi()

	@api.multi
	def action_draft(self):
		self.state = 'draft'


	def action_valid(self):
		for line in self.line_ids:
			for komb in line.kombinasi_ids:
					if self.taks_periode == 'maret':
						area = self.env['ka_plantation.register.line'].search([
							('kecamatan_id', '=', line.kecamatan_id.id),
							('intensifikasi_id','=',komb.intensifikasi_id.id),
							('varietas_id','=',komb.varietas_id.id),
							('mtt_id','=',self.mtt_id.id)])
						if area:
							for a in area:
								# a.taks_produksi = komb.produktivitas * a.luas
								# a.produktivitas = komb.produktivitas
								print a.area_id.code
								print a.taks_produksi
					if self.taks_periode == 'desember':
						area = self.env['ka_plantation.area.agronomi'].search([
							('kecamatan_id', '=', line.kecamatan_id.id),
							('intensifikasi_id','=',komb.intensifikasi_id.id),
							('varietas_id','=',komb.varietas_id.id),
							('mtt_id','=',self.mtt_id.id)])
						for a in area:
							a.taks_produksi = komb.produktivitas * a.luas
		self.state = 'valid'

	@api.multi
	def open_pivot_table(self):
		if self.taks_periode == 'desember':
			action = self.env.ref('ka_tanaman.action_show_pivot_desember')
			result = action.read()[0]
			result['domain'] = [('mtt_id', '=', (self.mtt_id.id,))]
			return result
		if self.taks_periode == 'maret':
			action = self.env.ref('ka_tanaman.action_show_pivot_maret')
			result = action.read()[0]
			result['domain'] = [('mtt_id', '=', (self.mtt_id.id,))]
			return result

	def cetak_taksasi(self, param_wizard):
		report_obj = self.env['report']
		template = 'ka_tanaman.hasil_taksasi_view'
		report = report_obj._get_report_from_name(template)
		domain = {
			'company_id':self.company_id.id,
			'kecamatan_id': param_wizard['kecamatan_id'],
			'desa_id': param_wizard['desa_id'],
			'taksasi': param_wizard['taksasi'],
			'wilayah': param_wizard['wilayah']
		}
		vals = {
			'ids': self.ids,
			'model':report.model,
			'form':domain
		}
		
		return report_obj.get_action(self, template, data=vals)

	def cetak_estimasi(self):
		report_obj = self.env['report']
		template = 'ka_tanaman.estimasi_perolehan_view'
		report = report_obj._get_report_from_name(template)
		domain = {
			'company_id':self.company_id.id,
		}
		vals = {
			'ids': self.ids,
			'model':report.model,
			'form':domain
		}
		
		return report_obj.get_action(self, template, data=vals)


class AreaSamplingLine(models.Model):
	_name = 'ka_plantation.sampling.line'

	sampling_id = fields.Many2one('ka_plantation.sampling',string="Sampling")
	kecamatan_id = fields.Many2one('res.kecamatan',string="Nama Kecamatan",readonly=True)
	jumlah_petak = fields.Integer(string="Jumlah Petak",readonly=True)
	jumlah_intensifikasi = fields.Integer(string="Jumlah Intensifikasi",readonly=True)
	jumlah_varietas = fields.Integer(string="Jumlah Varietas",readonly=True)
	luas_petak = fields.Float(string="Luas Petak",readonly=True)
	jumlah_sampling = fields.Integer(string="Jumlah Sampling",readonly=True)
	mtt_id = fields.Many2one(related='sampling_id.mtt_id',string="MTT",readonly=True)
	company_id = fields.Many2one('res.company', string='Company',readonly=True, required=True,default=lambda self: self.env['res.company']._company_default_get('ka_plantation.sampling.area'))
	sampling_taksasi_ids = fields.One2many('ka_plantation.sampling.taksasi','sampling_line_id',string="Taksasi")
	kombinasi_ids = fields.One2many('ka_plantation.sampling.kombinasi','kombinasi_id',string="Kombinasi")
	rata_produktivitas = fields.Float("Produktivitas(Ku/ha)",compute='_compute_rata_produktivitas')
	taks_produksi = fields.Float(string="Taks. Produksi(Ku)",compute='_compute_taks_produksi')

	@api.multi
	def open_list_intensifikasi(self):
		self._cr.execute("""SELECT 
								a.intensifikasi_id
							FROM 
								ka_plantation_area_agronomi a 
							INNER JOIN 
								ka_plantation_area b ON a.area_id = b.id
							INNER JOIN 
								res_kecamatan c ON b.kecamatan_id = c.id
							WHERE 
									a.intensifikasi_id IS NOT NULL 
								AND 
									a.varietas_id IS NOT NULL 
								AND 
									b.status_polygon = 'valid'
								AND
									c.id = %s
								AND 
									a.mtt_id = %s
							GROUP BY 
								a.intensifikasi_id;""",(str(self.kecamatan_id.id),str(self.mtt_id.id),))
		intensifikasi = self._cr.fetchall()
		
		action = self.env.ref('ka_tanaman.action_show_intensifikasi')
		result = action.read()[0]
		result['domain'] = [('id', 'in', intensifikasi)]
		return result

	@api.multi
	def open_list_varietas(self):
		self._cr.execute("""SELECT 
								a.varietas_id
							FROM 
								ka_plantation_area_agronomi a 
							INNER JOIN 
								ka_plantation_area b ON a.area_id = b.id
							INNER JOIN 
								res_kecamatan c ON b.kecamatan_id = c.id
							WHERE 
									a.varietas_id IS NOT NULL 
								AND 
									a.varietas_id IS NOT NULL 
								AND 
									b.status_polygon = 'valid'
								AND 
									c.id = %s
								AND 
									a.mtt_id = %s
							GROUP BY a.varietas_id;""",(str(self.kecamatan_id.id),str(self.mtt_id.id),))
		varietas = self._cr.fetchall()
		action = self.env.ref('ka_tanaman.action_show_varietas')
		result = action.read()[0]
		result['domain'] = [('id', 'in', varietas)]
		return result

	def search_petak_id(self):
		petak_ids = []
		for i in self.get_kombinasi():
			self._cr.execute("""SELECT 
									DISTINCT a.area_id as area_id,
									a.id,
									a.luas
								FROM 
									ka_plantation_area_agronomi a 
								INNER JOIN 
									ka_plantation_area b ON a.area_id = b.id
								INNER JOIN 
									res_kecamatan c ON b.kecamatan_id = c.id
								WHERE 
										a.intensifikasi_id = %s 
									AND 
										a.varietas_id = %s
									AND 
										b.status_polygon = 'valid'
									AND 
										cast(substring(b.code,char_length(b.code)) AS TEXT) ~ '^[0-9]'
									AND 
										MOD(cast(substring(b.code,char_length(b.code)) AS INT),2)=1
									AND 
										c.id = %s
									AND 
										a.mtt_id = %s
								GROUP BY 
									a.id
								ORDER BY
									a.area_id
								LIMIT %s;""",(str(i[1]),str(i[0]),str(self.kecamatan_id.id),str(self.mtt_id.id),str(self.jumlah_sampling),))
			petak = self._cr.fetchall()
			petak_ids.extend(petak)
		return petak_ids

	def create_sampling_taksasi(self):
		self._cr.execute("DELETE FROM ka_plantation_sampling_taksasi WHERE sampling_line_id = %s;",(self.id,))
		for j in self.search_petak_id():
			data ={
						'sampling_line_id': self.id,
						'kecamatan_id' : self.kecamatan_id.id,
						'area_id' : j[0],
						'jumlah' : 0,
						'tinggi' : 0,
						'bobot' : 0,
						'faktor' : 0,
						'luas_contoh' : j[2],
					}
			self.env['ka_plantation.sampling.taksasi'].create(data)

	@api.multi
	def open_list_petak(self):
		register_ids = []
		for j in self.search_petak_id():
			register_ids.append(j[1])

		action = self.env.ref('ka_tanaman.action_show_agronomi')
		result = action.read()[0]
		result['domain'] = [('id', 'in', register_ids)]
		return result

	@api.onchange('sampling_taksasi_ids')
	def _compute_rata_produktivitas(self):
		# return
		for s in self:
			taks = ([taksasi.produktivitas_petak for taksasi in s.sampling_taksasi_ids])
			if len(taks) > 0:
				s.rata_produktivitas = sum(taks) / len(taks)

	def get_kombinasi(self):
		self._cr.execute("""SELECT 
								a.varietas_id,
								a.intensifikasi_id
							FROM 
								ka_plantation_area_agronomi a 
							INNER JOIN 
								ka_plantation_area b ON a.area_id = b.id
							INNER JOIN 
								res_kecamatan c ON b.kecamatan_id = c.id
							WHERE 
									a.intensifikasi_id IS NOT NULL 
								AND 
									a.varietas_id IS NOT NULL 
								AND 
									b.status_polygon = 'valid'
								AND 
									c.id = %s
								AND 
									a.mtt_id = %s
							GROUP BY 
							a.varietas_id, a.intensifikasi_id;""",(str(self.kecamatan_id.id),str(self.mtt_id.id),))
		kombinasi = self._cr.fetchall()
		return kombinasi

	def create_sampling_kombinasi(self):
		self._cr.execute("DELETE FROM ka_plantation_sampling_kombinasi WHERE kombinasi_id = %s;",(self.id,))
		for kombinasi in self.get_kombinasi():
			data = {
				'kombinasi_id' : self.id,
				'kecamatan_id' : self.kecamatan_id.id,
				'intensifikasi_id' : kombinasi[1],
				'varietas_id' : kombinasi[0],
				'produktivitas_varint' : 0
			}
			self.env['ka_plantation.sampling.kombinasi'].create(data)

	@api.multi
	@api.onchange('sampling_taksasi_ids')
	def _compute_taks_produksi(self):
		for s in self:
			if s.sampling_id.taks_periode == 'maret':
				s._cr.execute("""SELECT sum(a.taks_produksi)
									FROM 
										ka_plantation_register_line a
									WHERE
										a.mtt_id = %s
									AND
										a.register_type = %s
									AND
										a.kecamatan_id = %s;""",(str(s.mtt_id.id),'tr',str(s.kecamatan_id.id),))
				taksasi = s._cr.fetchall()
				for t in taksasi:
					s.taks_produksi = t[0]
			if s.sampling_id.taks_periode == 'desember':
				s._cr.execute("""SELECT sum(a.taks_produksi)
									FROM 
										ka_plantation_area_agronomi a
									WHERE
										a.mtt_id = %s
									AND
										a.register_type = %s
									AND
										a.kecamatan_id = %s;""",(str(s.mtt_id.id),'tr',str(s.kecamatan_id.id),))
				taksasi = s._cr.fetchall()
				for t in taksasi:
					s.taks_produksi = t[0]