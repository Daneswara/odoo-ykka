# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields

class KaHrConfig(models.Model):
	"""Setting for `hr` modules, which call in `ka_hr_pegawai.config.wizard`.
	This model just only have 1 record for config, so the `ka_hr_pegawai.config.wizard` only call first record.

	_name = 'hr.config'
	"""

	_name = 'hr.config'

	hr_status_staf_id = fields.Many2one('hr.employee.status', string="Status Staf",
		help="Pilih status karyawan untuk 'Staf'.")
	hr_status_pelaksana_id = fields.Many2one('hr.employee.status', string="Status Pelaksana",
		help="Pilih status karyawan untuk 'Pelaksana'.")
	hr_pensiun_age = fields.Integer(string="Usia Pensiun", default=55,
		help="Untuk menentukan usia pensiun dari karyawan.")
	hr_mpp_month = fields.Integer(string="Bulan MPP", default=4,
		help="Untuk menentukan jumlah bulan MPP sebelum pensiun.")
