# ----------------------------------------------------------
# Data SP (Surat Pesanan) / PO (Purchase Order)
# inherit 'purchase.order'
# ----------------------------------------------------------

from odoo import models, fields, api, exceptions

class logistik_sp(models.Model):
	_inherit = 'purchase.order'

	spp_id = fields.Many2one('logistik.spp', string='Nomor SPP', readonly=True)
	tender_id = fields.Many2one('logistik.tender', string='No. Tender', states={'approved': [('readonly', True)]})
	
	# @override
	@api.model
	def name_search(self, name='', args=None, operator='ilike', limit=100):
		context = self._context
		if context.has_key('product_id'):
			pid = context['product_id']
			self._cr.execute("""SELECT a.id
					FROM purchase_order a 
					JOIN purchase_order_line b 
					ON a.id = b.order_id WHERE b.product_id=%d and a.company_id=%d order by a.date_order desc""" %(pid, self.env.user.company_id.id))
			ids = []
			for f in self._cr.fetchall():
				ids.append(f[0])

			repeat = self.browse(ids)
			return repeat.name_get()
			
		else:
			return super(logistik_sp, self).name_search(name, args, operator, limit)

	# @override
	@api.one
	def _get_picking_in(self, company_id):
		type_obj = self.env['stock.picking.type']
		picking_type_id = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
		if not picking_type_id:
			picking_type_id = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
			if not picking_type_id:
				raise exceptions.Warning("Make sure you have at least an incoming picking type defined!")
				return
		return picking_type_id
	
	
class purchase_order_line(models.Model):
	_inherit = "purchase.order.line"
	
	spm_line_id = fields.Many2one('logistik.spm.lines', 'SPM Line')
