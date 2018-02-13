from odoo import models, fields, api

class logistik_spm(models.Model):
	_inherit = 'product.template'
 
	_status_compute_last_order = False
 
	last_order = fields.Date(compute='_compute_last_order', string='TBTE', type='date')
	last_order_id = fields.Many2one('purchase.order', compute='_compute_last_order', string='No SP')
 	
	@api.multi
	def _compute_last_order(self):
		if self._status_compute_last_order:
			return
 
		self._status_compute_last_order = True
		ids = [s.id for s in self]
 
		self._cr.execute('''SELECT DISTINCT ON(p.id)
			p.id, o.date_order, l.order_id FROM purchase_order_line l
			JOIN purchase_order o ON o.id = l.order_id
			RIGHT OUTER JOIN product_product p ON p.id = l.product_id
			WHERE p.id IN %s ORDER BY 1, 2 DESC''', (tuple(ids),))
 
		fetch = self._cr.fetchall()
		for pid, odate, order_id in fetch:
			for s in self:
				if s.id == pid:
					s.last_order = odate
					s.last_order_id = order_id