from odoo import models, fields, api
import time

class logistik_sp_cancel(models.TransientModel):
	_name = 'logistik.sp.cancel'
	_description = "Wizard canceling logistik sp"

	back_tender = fields.Boolean(string='Apakah batalkan SP dan kembali ke SPPH tender?')
	back_agen = fields.Boolean(string='Apakah batalkan SP dan kembali ke SPPH agen?')
	golongan = fields.Char(string='Golongan', size=64)
	alasan = fields.Char(string='Alasan', required=True)

	@api.model
	def default_get(self, fields_list):
		active_id = self._context and self._context.get('active_id')
		po = self.env['purchase.order'].browse(active_id)
		res = super(logistik_sp_cancel, self).default_get(fields_list)
		res.update(golongan = po.golongan)
		return res

	@api.one
	def do_cancel_logistik_sp(self):
		active_id = self._context and self._context.get('active_id')
		po = self.env['purchase.order'].browse(active_id)
		po.action_cancel(self.back_tender, self.back_agen, self.alasan)
		# cancel dest PO
		source_uid  =  self.env.user.company_id.intercompany_user_id.id
		ou_company = po.sudo(source_uid).operating_unit_id.get_company_ref()[0]
		dest_po_src = self.env['purchase.order'].sudo(source_uid).with_context(company_id=ou_company.id).search([('source_order_id','=',po.id)], limit=1)
		if dest_po_src:
			dest_po_src.sudo(source_uid).with_context(company_id=ou_company.id).action_cancel(self.back_tender, self.back_agen, self.alasan)
