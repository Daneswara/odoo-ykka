from odoo import models, fields, api

class logistik_spm_nomor(models.TransientModel):
	_name = 'logistik.spm.nomor'
	_description = "Nomor SPM"
	
	no_spm = fields.Char(string='Nomor SPM', size=12)

	@api.one
	def action_nomor_spm(self):
		active_id = self._context and self._context.get('active_id', False) or False
		obj_spm = self.env['logistik.spm'].browse(active_id)
		obj_spm.action_number(self.no_spm)
		return {'type': 'ir.actions.act_window_close'}