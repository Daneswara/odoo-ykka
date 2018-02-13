from odoo import models, fields, api

class Periode(models.Model):
	_name = 'ka_plantation.periode'
	_description = "Periode masa tanam & tebang"
	_order = 'name'
	_rec_name = 'name'

	name = fields.Char(string="Kode", size=3, required=True)
	keterangan = fields.Char(string="Keterangan", required=True)

	_sql_constraints = [
		('periode_code_unique', 'UNIQUE(name)', 'Kode sudah ada, silahkan masukkan kode lain!')
	]