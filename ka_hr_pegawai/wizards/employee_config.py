# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api

class KaHrPegawaiConfigWizard(models.TransientModel):
	"""models.TransientModel setting for `hr` modules which saved on `hr.config`.

	_name = ka_hr_pegawai.config.wizard
	"""

	_name = 'ka_hr_pegawai.config.wizard'

	def default_config(self):
		"""To get default config from `hr.config` model.
		Query `hr.config` for first record only.
		"""
		config = self.env['hr.config'].search([], order='id asc', limit=1)
		if not config:
			config = self.env['hr.config'].create({'hr_pensiun_age': 55, 'hr_mpp_month': 4})
			self._cr.commit()
		return config

	hr_config_id = fields.Many2one('hr.config', string="Config", default=default_config)
	hr_status_staf_id = fields.Many2one(string="Status Staf", related='hr_config_id.hr_status_staf_id',
		domain=[('parent_id', '=', None)] ,help="Pilih status karyawan untuk 'Staf'.")
	hr_status_pelaksana_id = fields.Many2one(string="Status Pelaksana", related='hr_config_id.hr_status_pelaksana_id',
		domain=[('parent_id', '=', None)], help="Pilih status karyawan untuk 'Pelaksana'.")
	hr_pensiun_age = fields.Integer(string="Usia Pensiun", related='hr_config_id.hr_pensiun_age',
		help="Untuk menentukan usia pensiun dari karyawan.")
	hr_mpp_month = fields.Integer(string="Bulan MPP", related='hr_config_id.hr_mpp_month',
		help="Untuk menentukan jumlah bulan MPP sebelum pensiun.")

	@api.multi
	def save_data(self):
		"""To save data in `hr.config` model.

		Decorators:
			api.multi
		"""
		self.hr_config_id.hr_status_staf_id = self.hr_status_staf_id
		self.hr_config_id.hr_status_pelaksana_id = self.hr_status_pelaksana_id
		self.hr_config_id.hr_pensiun_age = self.hr_pensiun_age
		self.hr_config_id.hr_mpp_month = self.hr_mpp_month
