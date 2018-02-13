from odoo import models, fields, api, exceptions

class logistik_tender_rekanan(models.TransientModel):
	_name = "logistik.tender.rekanan"
	_description = "Pembelian Tender Rekanan"

	rekanan_id = fields.Many2one('res.partner', string='Rekanan', required=True)

	@api.model
	def view_init(self, fields_list):
		record_id = self._context and self._context.get('active_id', False) or False
		tender = self.env['logistik.tender'].browse(record_id)
		if not tender.line_ids:
			raise exceptions.Warning('Barang tidak ditemukan di tender!')
			return
		return super(logistik_tender_rekanan, self).view_init(fields_list)

	@api.one
	def create_spp(self):
		active_id = self._context and self._context.get('active_id', [])
		tender = self.env['logistik.tender'].browse(active_id)
		tender.create_spp(self.rekanan_id.id)
		return {'type': 'ir.actions.act_window_close'}