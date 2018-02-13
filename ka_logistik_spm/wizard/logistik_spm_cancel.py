from odoo import models, fields, api

class logistik_spm_cancel(models.TransientModel):
	_name = 'logistik.spm.cancel'
	_description = 'SPM Batal'

	cancel_reason = fields.Text(string='Alasan Pembatalan', required=True)
	cancel_by = fields.Many2one('res.users', string='Dibatalkan Oleh', readonly=True, default=lambda self: self._uid)
	cancel_date = fields.Date(string='Tanggal Dibatalkan', readonly=True, default=fields.Date.today)

	@api.one
	def do_spm_cancel(self):
		active_id = self._context and self._context.get('active_id', False) or False
		spm_line = self.env['logistik.spm.lines'].browse(active_id)
		spm_line.action_cancel(self)
		return {'type': 'ir.actions.act_window_close'}