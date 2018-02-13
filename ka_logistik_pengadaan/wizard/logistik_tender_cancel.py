from odoo import models, fields, api

class logistik_tender_cancel(models.TransientModel):
	_name = "logistik.tender.cancel"
	_description = "Tender Batal"

	cancel_reason = fields.Text(string='Alasan Pembatalan', required=True)
	cancel_by = fields.Many2one('res.users', string='Dibatalkan Oleh', readonly=True, default=lambda self: self._uid)
	cancel_date = fields.Date(string='Tanggal Dibatalkan', readonly=True, default=fields.Date.today)

	# @api.model
	# def default_get(self, fields_list):
		# res = super(logistik_tender_cancel, self).default_get(fields_list)
		# record_id = self._context and self._context.get('active_id', False) or False
		# res.update(tender_id = record_id)
		# return res

	@api.one
	def tender_cancel(self):
		active_id = self._context and self._context.get('active_id', False) or False
		tender = self.env['logistik.tender'].browse(active_id)
		tender.action_cancel(self)
		return {'type': 'ir.actions.act_window_close'}