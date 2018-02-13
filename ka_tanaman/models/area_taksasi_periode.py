from odoo import models, fields, api
from datetime import datetime

class TaksasiAreaPeriode(models.Model):
	_name = 'ka_plantation.area.taksasi.periode'
	_order = 'code'

	code = fields.Char(string="Kode", size=24, required=True)
	name = fields.Char(string="Nama", required=True)
	bulan = fields.Selection([
		(1, "Januari"),
		(2, "Pebruari"),
		(3, "Maret"),
		(4, "April"),
		(5, "Mei"),
		(6, "Juni"),
		(7, "Juli"),
		(8, "Agustus"),
		(9, "September"),
		(10, "Oktober"),
		(11, "Nopember"),
		(12, "Desember"),
	], string="Bulan", default=datetime.now().date().month)
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)

	_sql_constraints = [
		('area_taksasi_periode_code_unique', 'UNIQUE(code)', 'Kode sudah ada, silahkan masukkan kode lain!')
	]