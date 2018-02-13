# -------------------------------------------------------------
# Wizard untuk import data dari ka_fingerspot ke hr.attendance
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# -------------------------------------------------------------

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from math import modf

class KaHrFingerspotAttendanceImportWizard(models.TransientModel):
	_name = 'ka_hr.fingerspot.attendance.import.wizard'

	date_from = fields.Date(string="Tanggal Awal", required=True, default=fields.Date.today)
	date_to = fields.Date(string="Tanggal Akhir", required=True, default=fields.Date.today)
	company_id = fields.Many2one('res.company', string="Unit/PG", default=lambda self: self.env.user.company_id)

	def _get_date_list(self):
		date_awal = datetime.strptime(self.date_from, DATE_FORMAT).date()
		date_akhir = datetime.strptime(self.date_to, DATE_FORMAT).date()

		selisih = (date_akhir - date_awal).days

		date_list = [date_awal + timedelta(days=i) for i in range(selisih+1)]
		return date_list

	def _get_jakarta_timezone(self, utc_datetime):
		"""convert datetime timezone from UTC to asia/jakarta"""
		return utc_datetime + timedelta(hours=7)

	def _get_time_in_out(self, group, date_in):
		sql = """SELECT b.time_in, b.time_out FROM hr_attendance_group_shift a 
				INNER JOIN hr_attendance_shift b ON a.shift_id=b.id
				WHERE a.hr_attendance_group_id=%s AND a.date_end >='%s' and a.date_start <='%s'
				LIMIT 1""" %(str(group.id), date_in, date_in)

		self._cr.execute(sql)
		return self._cr.fetchone()

	def import_data(self):	
		date_list = self._get_date_list()
		scanlog = self.env['ka_fingerspot.scanlog'].search([('date_scan_date', 'in', date_list), ('company_id', 'child_of', self.company_id.id)], order='id asc')
		self.env['hr.attendance'].set_data_attendance(scanlog, self.company_id)