# ----------------------------------------------------------
# Data config setting cuti & absensi SDM
# inherit res.company
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ---------------------------------------------------------

from datetime import datetime, timedelta
from odoo import models, fields, api

class KaHrHolidaysResCompany(models.Model):
	_inherit = 'res.company'

	NO_CONFIG_MESSAGE = "Konfigurasi cuti belum diatur! Hubungi administrator untuk melanjutkan."

	hr_holidays_yearly_item = fields.Many2one('hr.holidays.status', string="Item Cuti Tahunan",
		domain=[('holiday_type', '=', 'add')])
	hr_holidays_yearly_periodic = fields.Integer(string="Periode Cuti Tahunan", default=1)
	hr_holidays_max_sisa_yearly = fields.Integer(string="Max. Sisa Cuti Tahunan", default=0)
	hr_holidays_big_item = fields.Many2one('hr.holidays.status', string="Item Cuti Besar",
		domain=[('holiday_type', '=', 'add')])
	hr_holidays_big_periodic = fields.Integer(string="Periode Cuti Besar", default=1)
	hr_holidays_max_sisa_big = fields.Integer(string="Max. Sisa Cuti Besar", default=0)
	hr_holidays_group_item = fields.Many2one('hr.holidays.status', string="Item Pengurang Cuti Bersama",
		domain=[('holiday_type', '=', 'remove'), ('leave_type', '=', 'cuti')])
	hr_holidays_inhaldagen_item = fields.Many2one('hr.holidays.status', string="Item Alokasi Cuti Inhaldagen",
		domain=[('holiday_type', '=', 'add')])
	hr_holidays_inhaldagen_expire = fields.Integer(string="Jumlah Kadaluwarsa Inhaldagen", default=30)

	hr_attendance_daily = fields.Selection([
		(1, "Senin - Jumat"),
		(2, "Senin - Sabtu")
	], string="Hari Kerja", required=True, default=1)

	def get_off_day(self):
		if self.hr_attendance_daily == 1:
			return [5, 6]
		else:
			return [5]

	def _get_jakarta_timezone(self, utc_datetime):
		"""convert datetime timezone from UTC to asia/jakarta"""
		return utc_datetime + timedelta(hours=7)

	def today_is_off_day(self):
		"""helper to check when today is off day"""
		date_obj = self._get_jakarta_timezone(datetime.now()).date()
		idx = date_obj.weekday()
		if idx in self.get_off_day():
			return True

		holidays = self.env['ka_hr.holidays.group'].search([
			('tgl_holiday', '=', date_obj)
		])

		if len(holidays) > 0:
			return True

		return False

	def check_requirement(self):
		return self.hr_holidays_yearly_item is not False and \
			self.hr_holidays_yearly_periodic > 0 and \
			self.hr_holidays_max_sisa_yearly is not False and \
			self.hr_holidays_big_item is not False and \
			self.hr_holidays_big_periodic > 0 and \
			self.hr_holidays_max_sisa_big is not False and \
			self.hr_holidays_group_item is not False and \
			self.hr_holidays_inhaldagen_item is not False and \
			self.hr_holidays_inhaldagen_expire > 0