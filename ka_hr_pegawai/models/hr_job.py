# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields

class KaHrJob(models.Model):
	"""Master data of employee job position.

	_inherit = 'hr.job'
	"""

	_inherit = 'hr.job'

	# level = fields.Selection([
	# 	(1, "I    - Direktur Utama"),
	# 	(2, "II   - Direktur"),
	# 	(3, "III  - Kepala Divisi"),
	# 	(4, "IV   - Kepala Bagian"),
	# 	(5, "V    - Kepala Seksi"),
	# 	(6, "VI   - Kepala Sub Seksi"),
	# 	(7, "VII  - Pelaksana Tetap"),
	# 	(8, "VIII - Pelaksana Harian"),
	# 	(9, "IX   - Pelaksana Kampanye")
	# ], string="Level Job", required=True)

	code = fields.Char(string="Kode", size=6)

	_sql_constraints = [
		('hr_job_unique', 'UNIQUE(code, address_id)', "Kode sudah digunakan! Silahkan menggunakan kode lainnya.")
	]
