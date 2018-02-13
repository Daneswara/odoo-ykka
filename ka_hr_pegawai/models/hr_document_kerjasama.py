# ----------------------------------------------------------
# Data dokument kerjasama yg dimiliki oleh SDM
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields, api

class hr_document_kerjasama(models.Model):
	_name = 'hr.document.kerjasama'
	_description = "SDM Dokumen Kerjasama"

	nomor = fields.Char(string="Nomor Perjanjian", required="True", size=64)
	tanggal_mulai = fields.Date(default=fields.Date.today, required=True)
	tanggal_akhir = fields.Date(default=fields.Date.today, required=True)
	partner_id = fields.Many2one('res.partner', string="Rekanan", required=True)
	isi_perjanjian = fields.Text(string="Isi Perjanjian", required=True)
	catatan = fields.Text(string="Catatan")
	doc_count = fields.Integer(string="Number of documents attached", compute='_get_attached_docs')
	company_id = fields.Many2one('res.company', string="Unit/PG", required=True, default=lambda self: self.env.user.company_id)

	# @override
	@api.multi
	def name_get(self):
		res = []
		for s in self:
			nomor = s.nomor or ''
			res.append((s.id, nomor))

		return res

	# @override
	@api.model
	def name_search(self, name='', args=None, operator='ilike', limit=80):
		if not args:
			args = []

		if name:
			record = self.search([('nomor', operator, name)] + args, limit=limit)
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