from odoo import models, fields, api

class purchase_order_line(models.Model):
	_inherit = 'purchase.order.line'

	@api.one
	def open_sp(self):
		return {
			'name': 'Surat Pesanan',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'purchase.order',
			'type': 'ir.actions.act_window',
			'res_id': self.order_id.id,
			'target': 'current',
			'context': self._context,
		}
