from odoo import models, fields, api

class logistik_sp(models.Model):
	_inherit = 'purchase.order'

	logistik_invoice_ids = fields.One2many('logistik.invoice', 'order_id', string='Tagihan')
	total_invoiced = fields.Float(string='Total', digits=(16, 2), readonly=True, compute='_compute_invoiced')
	invoice_balance = fields.Float(string='Sisa Tagihan', digits=(16, 2), readonly=True, compute='_compute_invoiced')
	
	@api.depends('logistik_invoice_ids.amount_untaxed')
	def _compute_invoiced(self):
		self.total_invoiced = sum(line.amount_untaxed for line in self.logistik_invoice_ids)
		self.invoice_balance = self.amount_total - self.total_invoiced