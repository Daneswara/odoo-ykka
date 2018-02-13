# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, exceptions
class product_update_hps(models.TransientModel):
	_name = "product.product.update.hps"
	_description = "Update HPS Barang"
	
	product_id = fields.Many2one('product.product', 'Barang', required=False)
	lst_price = fields.Float('Nilai HPS', required=True)
	
	@api.model
	def default_get(self, fields):
		res = super(product_update_hps, self).default_get(fields)
		active_id = self._context.get('active_ids', [])
		active_model = self._context.get('active_model', [])
		obj_model = self.env[active_model].browse(active_id)

		res.update(
			product_id = obj_model[0].product_id.id,
			lst_price = obj_model[0].product_id.lst_price
			)		
		return res
		
	@api.one
	def do_update(self):
		active_id = self._context.get('active_ids', [])
		active_model = self._context.get('active_model', [])
		obj_model = self.env[active_model].browse(active_id)
		new_hps = self.lst_price
		product = self.env['product.product'].browse(self.product_id.id)
		product.lst_price = new_hps
		obj_model.lst_price = new_hps
		return {'type': 'ir.actions.act_window_close'}
product_update_hps()
