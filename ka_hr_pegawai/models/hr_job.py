# ----------------------------------------------------------
# Data jabatan
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields, api

class KaHrJob(models.Model):
	_inherit = 'hr.job'

	"""
	Level Job Department:
		(1, 'I - Direktur Utama'),
		(2, 'II - Direktur'),
		(3, 'III - Kepala Divisi'),
		(4, 'IV - Kepala Bagian'),
		(5, 'V - Kepala Seksi'),
		(6, 'VI - Kepala Sub Seksi'),
		(7, 'VII - Pelaksana'),
	"""
	
	level = fields.Selection([
		(1, 'I'),
		(2, 'II'),
		(3, 'III'),
		(4, 'IV'),
		(5, 'V'),
		(6, 'VI'),
		(7, 'VII'),
	], string="Level Job", required=True)