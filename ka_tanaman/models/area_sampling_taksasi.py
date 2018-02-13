from odoo import models, fields, api

class AreaSamplingTaksasi(models.Model):
	_name = 'ka_plantation.sampling.taksasi'

	sampling_line_id = fields.Many2one('ka_plantation.sampling.line', string="Sampling Line", readonly=True)
	kecamatan_id = fields.Many2one('res.kecamatan',string="Nama Kecamatan", readonly=True)
	area_id = fields.Many2one('ka_plantation.area',string="No. Petak",readonly=True)
	# register_id = fields.Many2one()
	intensifikasi_id = fields.Many2one('ka_plantation.intensifikasi', string="Intensifikasi",store=True,compute="compute_area_id")
	varietas_id = fields.Many2one('ka_plantation.varietas', string="Varietas",store=True,compute="compute_area_id")
	# masa_tanam = fields.Many2one()
	jumlah = fields.Float(string="Jumlah Batang (batang)",required=True,digits=(3,2))
	tinggi = fields.Float(string="Tinggi Batang (m/batang)",required=True,digits=(3,2))
	bobot = fields.Float(string="Bobot Batang (Kg/m)",required=True,digits=(3,2))
	faktor = fields.Float(string="Faktor Kebun",required=True,digits=(3,2))
	luas_contoh = fields.Float(related='area_id.luas',string="Luas Petak (Ha)",required=True,digits=(3,2))
	bobot_juring = fields.Float(string="Bobot Per Juring (Kg/juring)",compute='_compute_juring',digits=(3,2),readonly=True)
	bobot_petak = fields.Float(string="Bobot Petak Contoh (Ku)",compute='_compute_petak',digits=(3,2),readonly=True)
	# produktivitas_juring = fields.Float(string="Produktivitas Juring (Ku/Ha)",compute='_compute_produktivitas_juring',digits=(3,2),readonly=True)
	# produktivitas_petak = fields.Float(string="Produktivitas Petak (Ku/Ha)",compute='_compute_produktivitas_petak',digits=(3,2),readonly=True)
	produktivitas_petak = fields.Float(string="Produktivitas Petak (Ku/Ha)",compute='_compute_produktivitas_petak',digits=(3,2),readonly=True)
	produktivitas_varint = fields.Float(string="Produktivitas Varietas & Intensifikasi (Ku/Ha)",digits=(3,2),readonly=True)
	mtt_id = fields.Many2one(related='sampling_line_id.mtt_id',string="MTT")
	company_id = fields.Many2one('res.company', string='Company',readonly=True, required=True,default=lambda self: self.env['res.company']._company_default_get('ka_plantation.sampling.area'))
	rata_luas = fields.Float(related='sampling_line_id.sampling_id.rata_luas',string="Rata Luas")

	# @api.onchange('sampling_line_id')
	# def onchange_sampling_line(self):
	# 	print '------------check sampling line---------------'
	# 	print self.sampling_line_id

	# temp_id = None

	@api.multi
	@api.depends('jumlah','tinggi','bobot')
	def _compute_juring(self):
		for s in self:
			s.bobot_juring = s.jumlah *  s.tinggi * s.bobot

	@api.multi
	@api.depends('faktor', 'bobot_juring')
	def _compute_petak(self):
		for s in self:
			s.bobot_petak = ((s.bobot_juring * s.faktor) / 100) * s.luas_contoh
			#dibagi luaspetak lagi

	@api.multi
	@api.depends('bobot_petak', 'luas_contoh')
	def _compute_produktivitas_petak(self):
		for s in self:
			s.produktivitas_petak = s.bobot_petak / s.luas_contoh

	# @api.depends('produktivitas_juring','rata_luas')
	# def _compute_produktivitas_petak(self):
	# 	# return
	# 	for s in self:
	# 		print s.sampling_line_id
	# 		print s.sampling_line_id.sampling_id
	# 		print s.rata_luas
	# 		# if s.produktivitas_juring > 0:
	# 			# s.produktivitas_petak = s.produktivitas_juring /s.sampling_line_id.sampling_id.rata_luas

	# @api.onchange('produktivitas_petak')
	# def _compute_produktivitas_varint(self):
	# 	# return
	# 	for s in self:
	# 		if s.produktivitas_petak > 0:
	# 			s.produktivitas_varint = s.produktivitas_juring /s.sampling_line_id.sampling_id.jumlah_int_var


	@api.depends('area_id')
	def compute_area_id(self):
		for s in self:
			agronomi = s.env['ka_plantation.area.agronomi'].search([('area_id', '=', s.area_id.id),('mtt_id','=',s.mtt_id.id)])
			if agronomi:
				s.varietas_id = agronomi.varietas_id.id
				s.intensifikasi_id = agronomi.intensifikasi_id.id


class AreaSamplingKombinasi(models.Model):
	_name = 'ka_plantation.sampling.kombinasi'

	kombinasi_id = fields.Many2one('ka_plantation.sampling.line', string="Sampling Line", readonly=True)
	kecamatan_id = fields.Many2one('res.kecamatan',string="Nama Kecamatan", readonly=True)
	intensifikasi_id = fields.Many2one('ka_plantation.intensifikasi', string="Intensifikasi",store=True,readonly=True)
	varietas_id = fields.Many2one('ka_plantation.varietas', string="Varietas",store=True,readonly=True)
	produktivitas = fields.Float(string="Produktivitas Kombinasi",digits=(3,2),readonly=True,compute="_compute_produktivitas_varint")
	mtt_id = fields.Many2one(related='kombinasi_id.mtt_id',string="MTT")
	company_id = fields.Many2one('res.company', string='Company',readonly=True, required=True,default=lambda self: self.env['res.company']._company_default_get('ka_plantation.sampling.area'))
	taks_periode = fields.Selection(string="Periode taksasi",related="kombinasi_id.sampling_id.taks_periode")

	def _compute_produktivitas_varint(self):
		for s in self:
			list_kombinasi = []
			periode = ""
			rec = s.env['ka_plantation.sampling.taksasi'].search([('sampling_line_id', '=', s.kombinasi_id.id),('kecamatan_id', '=', s.kecamatan_id.id),('intensifikasi_id','=',s.intensifikasi_id.id),('varietas_id','=',s.varietas_id.id)])
			for x in rec:
				list_kombinasi.append(x.produktivitas_petak)
				periode = x.sampling_line_id.sampling_id.taks_periode
			if len(list_kombinasi) > 0:
				if s.taks_periode == periode:
					s.produktivitas = sum(list_kombinasi) / len(list_kombinasi)