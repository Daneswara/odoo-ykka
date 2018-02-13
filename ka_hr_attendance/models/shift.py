# ----------------------------------------------------------
# Data shift pegawai
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields, api

class KaHrAttendanceShift(models.Model):
	_name = 'hr.attendance.shift'
	_description = "SDM Shift Pegawai"

	name = fields.Char(string="Nama Shift", size=24, required=True)
	time_in = fields.Float(string="Jam Masuk", required=True)
	time_out = fields.Float(string="Jam Pulang", required=True)
	# tolerance = fields.Integer(string="Toleransi Masuk (menit)", required=True)
	company_id = fields.Many2one('res.company', string="Unit/PG", required=True, default=lambda self: self.env.user.company_id)