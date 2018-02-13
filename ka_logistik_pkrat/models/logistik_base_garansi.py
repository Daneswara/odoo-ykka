# ----------------------------------------------------------
# Data Garansi
# ----------------------------------------------------------

from odoo import models, fields

class logistik_base_garansi(models.Model):
	_name = 'logistik.base.garansi'
	_description = 'Satuan Garansi'

	kode = fields.Char(string='Kode', size=5, required=True)
	name = fields.Char(string='Keterangan', size=64, required=True)

	_sql_constraints = [
		('kode_unique', 'unique(kode)', 'Kode garansi tidak boleh dobel!')
	]