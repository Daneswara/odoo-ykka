# ----------------------------------------------------------
# Data dokument aset yg dimiliki oleh SDM
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields, api

class hr_document_asset(models.Model):
	_name = 'hr.document.asset'
	_description = "SDM Dokumen Aset"

	nomor_sertifikat = fields.Char(string="Nomor sertifikat", required=True, size=128)
	tanggal_terbit_sertifikat = fields.Date(string="Tanggal terbit", default=fields.Date.today)
	tanggal_akhir_sertifikat = fields.Date(string="Tanggal akhir", default=fields.Date.today)
	lokasi = fields.Char(string="Lokasi", required=True, size=255)
	desa_kelurahan_id = fields.Many2one('res.desa.kelurahan', string="Desa / Kelurahan", required=True)
	kecamatan_id = fields.Many2one(related='desa_kelurahan_id.kecamatan_id', string="Kecamatan", required=True)
	kab_kota_id = fields.Many2one(related='kecamatan_id.kab_kota_id', string="Kabupaten / Kota", required=True)
	provinsi_id = fields.Many2one(related='kab_kota_id.provinsi_id', string="Provinsi", required=True)
	luas = fields.Float(string="Luas (%s)" % (u"\u33A1"))
	jenis_sertifikat = fields.Selection([
		('hm', 'HM'),
		('hgb', 'HGB'),
		('hgu', 'HGU'),
		('hp', 'HP'),
		('hpl', 'HPL'),
	], string="Jenis sertifikat", required=True)
	catatan = fields.Text(string="Catatan")
	company_id = fields.Many2one('res.company', string="Unit/PG", required=True, default=lambda self: self.env.user.company_id)
	doc_count = fields.Integer(string="Number of documents attached", compute='_get_attached_docs')

	# @override
	@api.multi
	def name_get(self):
		res = []
		for s in self:
			nomor = s.nomor_sertifikat or ''
			res.append((s.id, nomor))

		return res

	# @override
	@api.model
	def name_search(self, name='', args=None, operator='ilike', limit=80):
		if not args:
			args = []

		if name:
			record = self.search([('nomor_sertifikat', operator, name)] + args, limit=limit)
		else:
			record = self.search(args, limit=limit)

		return record.name_get()

	@api.multi
	def _get_attached_docs(self):
		"""
		Untuk menghitung (compute) jumlah dokumen yg di attach
		"""
		attachment = self.env['ir.attachment']
		for s in self:
			s.doc_count = attachment.search_count([('res_model', '=', s._name), ('res_id', '=', s.id)])

	@api.multi
	def attachment_tree_view(self):
		"""
		Untuk melihat attachment pada dokumen
		"""
		ids = [s.id for s in self]
		domain = [('res_model', '=', self._name), ('res_id', 'in', ids)]
		res_id = ids and ids[0] or False
		return {
			'name': 'Attachments',
			'domain': domain,
			'res_model': 'ir.attachment',
			'type': 'ir.actions.act_window',
			'view_id': False,
			'view_mode': 'kanban,tree,form',
			'view_type': 'form',
			'limit': 80,
			'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, res_id)
		}