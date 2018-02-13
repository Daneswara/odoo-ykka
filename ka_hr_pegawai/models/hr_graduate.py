# ----------------------------------------------------------
# Data pendidikan
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields

class hr_graduate(models.Model):
	_name = 'hr.graduate'
	_description = "SDM Pendidikan"

	name = fields.Char(string='Nama', size=32, required=True)