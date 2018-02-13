# ----------------------------------------------------------
# Data dokument perijinan yg dimiliki oleh SDM
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields, api

class hr_document_legal(models.Model):
	_name = 'hr.document.legal'
	_description = "SDM Dokumen Legal"

	name = fields.Char(string="Nama Dokumen", required=True, size=128)
	nomor = fields.Char(string="Nomor", required=True, size=32)
	state = fields.Selection([
		('on', "Berlaku"),
		('off', "Tidak Berlaku")
	], string="Status", default='on')
	tanggal_terbit = fields.Date(default=fields.Date.today)
	tanggal_akhir = fields.Date(default=fields.Date.today)
	doc_count = fields.Integer(string="Number of documents attached", compute='_get_attached_docs')
	catatan = fields.Text(string="Catatan")
	company_id = fields.Many2one('res.company', string="Unit/PG", required=True, default=lambda self: self.env.user.company_id)
	partner_id = fields.Many2one('res.partner', string="Instansi Penerbit", required=True)

	@api.multi
	def _get_attached_docs(self):
		"""
		Untuk menghitung (compute) jumlah dokumen yg di attach
		"""
		attachment = self.env['ir.attachment']
		for s in self:
			s.doc_count = attachment.search([('res_model', '=', s._name), ('res_id', '=', s.id)], count=True)

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

	@api.one
	def action_set_off(self):
		"""
		Set state 'off'
		"""
		return self.write({'state': 'off'})

	@api.one
	def action_set_on(self):
		"""
		Set state 'on'
		"""
		return self.write({'state': 'on'})