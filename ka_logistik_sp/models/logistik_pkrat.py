from odoo import models, fields, api

class logistik_pkrat(models.Model):
	_inherit = 'logistik.pkrat'

	_status_compute_total = False

	total_amount_sp = fields.Float(compute='_compute_total', string='Kontrak/SP', digits=(16, 2))
	rasio = fields.Float(compute='_compute_total', string='Progress', digits=(16, 2))

	@api.multi
	def _compute_total(self):
		if self._status_compute_total:
			return

		self._status_compute_total = True
		ids = [s.id for s in self]
		
		self._cr.execute('''SELECT pkrat.id as id, 
			SUM(l.product_qty*l.price_unit) AS total_sp, 
			SUM(l.product_qty*l.price_unit*100/pkrat.nilai) AS rasio
			FROM logistik_pkrat pkrat  
				JOIN account_analytic_account aa ON aa.id = pkrat.account_analytic_id
				LEFT JOIN purchase_order_line l ON aa.id = l.account_analytic_id
				WHERE pkrat.id IN %s GROUP BY 1''', (tuple(ids),))

		fetch = self._cr.fetchall()
		for pkrat_id, total_sp, rasio in fetch:
			for s in self:
				if s.id == pkrat_id:
					s.total_amount_sp = total_sp
					s.rasio = rasio