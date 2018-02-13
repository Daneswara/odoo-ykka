# ----------------------------------------------------------
# Data detail SPM (Surat Permintaan Material)
# inherit 'logistik.spm.lines'
# ----------------------------------------------------------

from odoo import models, fields, api, exceptions

class logistik_spm_lines(models.Model):
	_inherit = 'logistik.spm.lines'

	order_id = fields.Many2one('purchase.order', string='Nomor SP')
	repeat_order_line_id = fields.Many2one('purchase.order.line', string='Repeat SP')

	@api.multi
	def action_open_histori_harga(self):
		"""
		Buka data history harga
		"""
		mod_obj = self.env['ir.model.data']
		res = mod_obj.get_object_reference('ka_logistik_pengadaan', 'view_open_histori_harga')
		res_id = res and res[1] or False
		return {
			'name': 'Histori Harga',
			'view_type': 'form',
			'view_mode': 'tree',
			'context': self._context,
			'view_id': [res_id],
			'limit': 10,
			'domain': [('product_id', '=', self.product_id.id)],
			'res_model': 'purchase.order.line',
			'type': 'ir.actions.act_window',
			'target': 'new',
		}