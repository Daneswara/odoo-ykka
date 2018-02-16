# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields

class KaHrJob(models.Model):
	"""Manage employee jobs.

	Inherit: 'hr.job'
	"""

	_inherit = 'hr.job'

	level = fields.Selection([
		(1, "I    - Direktur Utama"),
		(2, "II   - Direktur"),
		(3, "III  - Kepala Divisi"),
		(4, "IV   - Kepala Bagian"),
		(5, "V    - Kepala Seksi"),
		(6, "VI   - Kepala Sub Seksi"),
		(7, "VII  - Pelaksana Tetap"),
		(8, "VIII - Pelaksana Harian"),
		(9, "IX   - Pelaksana Kampanye")
	], string="Level Job", required=True)
