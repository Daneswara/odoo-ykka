# ----------------------------------------------------------
# Data Denda
# ----------------------------------------------------------

from odoo import models, fields

class logistik_base_denda(models.Model):
	_name = 'logistik.base.denda'
	_description = 'Satuan Denda'

	kode = fields.Char(string='Kode', size=5, required=True)
	name = fields.Char(string='Keterangan', size=64, required=True)

	_sql_constraints = [
		('kode_unique', 'unique(kode)', 'Kode denda tidak boleh dobel!')
	]