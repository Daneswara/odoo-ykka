# ----------------------------------------------------------
# Data hubungan kerja pegawai
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields, api

class KaHrHubunganKerja(models.Model):
	_name = 'ka_hr.hubungan.kerja'
	_description = "SDM Hubungan Kerja"

	name = fields.Char(string="Hub. Kerja")