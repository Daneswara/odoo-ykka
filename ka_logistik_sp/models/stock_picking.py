from odoo import models, fields, api

# Create Invoice line from Stock Picking
# get account_id from jurnal_id (the origin code get from partner account)	
class stock_picking(models.Model):
	_inherit = 'stock.picking'

	def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):
		journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context)
		if context is None:
			context = {}
		partner, currency_id, company_id, user_id = key
		if inv_type in ('out_invoice', 'out_refund'):
			account_id = partner.property_account_receivable.id
			payment_term = partner.property_payment_term.id or False
		else:
			account_id = partner.property_account_payable.id
			if move.purchase_line_id.order_id.pengadaan == 'RD':
				account_id = journal.default_credit_account_id.id
			payment_term = partner.property_supplier_payment_term.id or False
		return {
			'origin': move.picking_id.name,
			'date_invoice': context.get('date_inv', False),
			'user_id': uid,
			'partner_id': partner.id,
			'account_id': account_id,
			'payment_term': payment_term,
			'type': inv_type,
			'fiscal_position': partner.property_account_position.id,
			'company_id': company_id,
			'currency_id': currency_id,
			'journal_id': journal_id,
		}