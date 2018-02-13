from odoo import models, fields, api, _

class stock_move(models.Model):
	_inherit = 'stock.move'

	def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type, context=None):
		fp_obj = self.pool.get('account.fiscal.position')
		# Get account_id
		if inv_type in ('out_invoice', 'out_refund'):
			account_id = move.product_id.property_account_income.id
			if not account_id:
				account_id = move.product_id.categ_id.property_account_income_categ.id
		else:
			account_id = move.product_id.property_account_expense.id
			if not account_id:
				account_id = move.product_id.categ_id.property_account_expense_categ.id
				category =  move.product_id.categ_id.parent_id
				while category and not account_id:
					account_id = category.property_account_expense_categ.id
					category = category.parent_id
					
			if not account_id:
				raise osv.except_osv(_('Error!'), _('Define an expense account for this product: "%s" (id:%d).') % (po_line.product_id.name, po_line.product_id.id,))
				
		fiscal_position = partner.property_account_position
		account_id = fp_obj.map_account(cr, uid, fiscal_position, account_id)

		# set UoS if it's a sale and the picking doesn't have one
		uos_id = move.product_uom.id
		quantity = move.product_uom_qty
		if move.product_uos:
			uos_id = move.product_uos.id
			quantity = move.product_uos_qty
		return {
			'name': move.name,
			'account_id': account_id,
			'product_id': move.product_id.id,
			'uos_id': uos_id,
			'quantity': quantity,
			'price_unit': self._get_price_unit_invoice(cr, uid, move, inv_type),
			'discount': 0.0,
			'account_analytic_id': False,
		}