# ----------------------------------------------------------
# Data Pegawai, inherit dari hr.employee
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from datetime import datetime, timedelta
from odoo import models, fields, api

class KaHrAttendanceEmployee(models.Model):
	_inherit = 'hr.employee'

	finger_id = fields.Many2one('ka_fingerspot.user', string="ID Fingerspot")
	hr_attendance_group_id = fields.Many2one('hr.attendance.group', string="Group Absensi")

	def _get_jakarta_timezone(self, utc_datetime):
		"""convert datetime timezone from UTC to asia/jakarta"""
		return utc_datetime + timedelta(hours=7)
	
	def get_date_now(self):
		datetime_now = self._get_jakarta_timezone(datetime.now())
		date_now = datetime_now.date()
		return date_now.strftime("%d-%m-%Y")

	def send_mail_check_in(self):
		template = self.env.ref('ka_hr_attendance.template_mail_no_check_in')
		self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)

	def send_mail_check_out(self):
		template = self.env.ref('ka_hr_attendance.template_mail_no_check_out')
		self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)

	@api.multi
	def action_view_attendance(self):
		action = self.env.ref('ka_hr_attendance.action_view_attendance_employee')
		result = action.read()[0]
		result['domain'] = [('employee_id', '=', self.id)]
		result['context'] = {'default_employee_id': self.id,
							'search_default_current_month':1}
		return result