# ----------------------------------------------------------
# Data config attendance / presensi SDM
# inherit res.company
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields

class KaHrAttendanceResCompany(models.Model):
	_inherit = 'res.company'

	hr_attendance_max_hour = fields.Integer(string="Max. Jam Kerja", default=16,
		help="Jumlah maksimal jam kerja dalam sehari.\nKaitannya dengan presensi check in & check out.")
	hr_attendance_weekly_report_send = fields.Selection([
		(0, "Senin"),
		(1, "Selasa"),
		(2, "Rabu"),
		(3, "Kamis"),
		(4, "Jumat"),
		(5, "Sabtu"),
		(6, "Minggu"),
	], string="Hari Laporan Presensi Mingguan")
	hr_attendance_weekly_check = fields.Selection([
		(0, "Senin"),
		(1, "Selasa"),
		(2, "Rabu"),
		(3, "Kamis"),
		(4, "Jumat"),
		(5, "Sabtu"),
		(6, "Minggu"),
	], string="Hari Analisa Presensi Mingguan", default=6,
		help="Analisa presensi mingguan.\nKaitannya dengan Surat Peringatan.\nDisarankan pilih pada hari minggu")
	hr_attendance_sp_late_weekly = fields.Integer(string="Hari Telat Mingguan", default=2,
		help="Jumlah hari telat dalam seminggu.")
	hr_attendance_sp_late_monthly = fields.Integer(string="Hari Telat Bulanan", default=3,
		help="Jumlah hari telat dalam sebulan.")