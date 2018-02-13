# ----------------------------------------------------------
# Data grouping presensi pegawai
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields, api

class KaHrAttendanceGroup(models.Model):
	_name = 'hr.attendance.group'
	_description = "SDM Grouping Presensi Pegawai"

	name = fields.Char(string="Nama Grup", size=64, required=True)
	company_id = fields.Many2one('res.company', string="Unit/PG", required=True, default=lambda self: self.env.user.company_id)
	group_shift_ids = fields.One2many('hr.attendance.group.shift', 'hr_attendance_group_id', string="Data Shift")

class KaHrAttendanceGroupShift(models.Model):
	_name = 'hr.attendance.group.shift'
	_description = "SDM Group Shift Pegawai"

	shift_id = fields.Many2one('hr.attendance.shift', string="Nama Shift", required=True)
	date_start = fields.Date(string="Mulai", required=True, index=True)
	date_end = fields.Date(string="Sampai", required=True, index=True)
	date_shift = fields.Date(string="Tanggal Shift", required=True, default=fields.Date.today)
	hr_attendance_group_id = fields.Many2one('hr.attendance.group', string="Nama Grup", required=True)