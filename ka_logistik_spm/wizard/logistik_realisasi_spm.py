import time
from odoo import models, fields, api, exceptions

#split and realisasikan SPM
class logistik_realisasi_spm(models.TransientModel):
	_name = 'logistik.realisasi.spm'
	_description = "Wizard Realisasi SPM Bertahap"

	saldo = fields.Float(string='Saldo SPM', digits=(11, 2), readonly=True)
	kuantum_sp = fields.Float(string='Kuantum Realisasi', digits=(11, 2), required=True)
	alasan = fields.Char(string='Alasan', size=64)
	save_ok = fields.Boolean(string='Save OK')
	
	@api.model
	def default_get(self, fields_list):
		active_model = self._context['active_model']
		res = super(logistik_realisasi_spm, self).default_get(fields_list)
		record_id = self._context and self._context.get('active_id', False) or False
		line = self.env[active_model].browse(record_id)
		if not line.product_id:
			raise exceptions.Warning('Kode barang belum didefinisikan!')
			return

		res.update(saldo = line.qty_saldo)
		return res

	@api.onchange('kuantum_sp')
	def onchange_kuantum_sp(self):
		self.save_ok = 0 < self.kuantum_sp < self.saldo
	
	@api.multi
	def action_simpan(self):
		self.ensure_one()
		active_id = self._context and self._context.get('active_id', False) or False
		spm_line = self.env['logistik.spm.lines'].browse(active_id)
		vals = {
			'parent_id': spm_line.id,
			'kuantum_sp': self.kuantum_sp, 
			'alasan': self.alasan,
		}
		return spm_line.action_realisasi_bertahap(vals)