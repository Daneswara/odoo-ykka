from odoo import models, fields, api

class res_partner(models.Model):
	_inherit = 'res.partner'

# 	status_transaksi = fields.Char(compute='_compute_status_transaksi', string='Status Transaksi')
# 
# 	@api.multi
# 	def _compute_status_transaksi(self):
# 		for s in self:
# 			s.status_transaksi = 'Transaksi Pasif' if not s.no_acc and not s.is_calon and s.purchase_order_count <= 0 else ''
				