from odoo import models, fields, api
import datetime

class logistik_sp_lines(models.Model):
	_inherit = 'purchase.order.line'
	_order = 'product_id'

	lst_price = fields.Float(related='product_id.lst_price', string='HPS', track_visibility='onchange', readonly=True)
	tanggal_sp = fields.Datetime(related='order_id.date_order', string='Order Date', readonly=True, store=True)
	spesifikasi = fields.Text(related='product_id.description', string='Spesifikasi', readonly=True)
	keterangan = fields.Text(string='Keterangan')

	def get_last_sp(self, prod_id, date_order, order_id):
		sp_date = datetime.datetime.strptime(date_order, "%Y-%m-%d %H:%M:%S") - datetime.timedelta(days=1)
		return self.search([('product_id', '=', prod_id), ('tanggal_sp', '<', date_order), ('order_id', '!=', order_id)], limit = 3, order = 'tanggal_sp desc')
		