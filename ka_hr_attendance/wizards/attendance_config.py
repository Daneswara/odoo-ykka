# ----------------------------------------------------------
# Data config setting presensi SDM
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ---------------------------------------------------------

from odoo import models, fields, api

class KaHrAttendanceConfigWizard(models.TransientModel):
	_name = 'ka_hr_attendance.config.wizard'

	company_id = fields.Many2one('res.company', string="Unit/PG", required=True, default=lambda self: self.env.user.company_id)
	
	""" hr_attendance_daily ada di ka_hr_holidays/models/res_company.py
	karena dibutuhkan untuk mengecek liburan, tp config nya ditaroh disini""" 
	hr_attendance_daily = fields.Selection([
		(1, "Senin - Jumat"),
		(2, "Senin - Sabtu")
	], related='company_id.hr_attendance_daily', string="Hari Kerja", required=True)
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
	], related='company_id.hr_attendance_weekly_report_send', string="Kirim Laporan Presensi Mingguan")
	hr_attendance_weekly_check = fields.Selection([
		(0, "Senin"),
		(1, "Selasa"),
		(2, "Rabu"),
		(3, "Kamis"),
		(4, "Jumat"),
		(5, "Sabtu"),
		(6, "Minggu"),
	], related='company_id.hr_attendance_weekly_check', string="Hari Analisa Presensi Mingguan", default=6,
		help="Analisa presensi mingguan.\nKaitannya dengan Surat Peringatan.\nDisarankan pilih pada hari minggu")
	hr_attendance_sp_late_weekly = fields.Integer(related='company_id.hr_attendance_sp_late_weekly',
		string="Hari Telat Mingguan", default=2, help="Jumlah hari telat dalam seminggu.")
	hr_attendance_sp_late_monthly = fields.Integer(related='company_id.hr_attendance_sp_late_monthly',
		string="Hari Telat Bulanan", default=3, help="Jumlah hari telat dalam sebulan.")

	@api.multi
	def save_data(self):
		self.company_id.hr_attendance_daily = self.hr_attendance_daily
		self.company_id.hr_attendance_max_hour = self.hr_attendance_max_hour
		self.company_id.hr_attendance_weekly_report_send = self.hr_attendance_weekly_report_send
		self.company_id.hr_attendance_weekly_check = self.hr_attendance_weekly_check
		self.company_id.hr_attendance_sp_late_weekly = self.hr_attendance_sp_late_weekly
		self.company_id.hr_attendance_sp_late_monthly = self.hr_attendance_sp_late_monthly