# -------------------------------------------------------------
# Wizard untuk mencetak data rekap presensi bulanan pegawai
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# -------------------------------------------------------------

from datetime import datetime
import calendar
from pprint import pprint
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

class KaHrAttendanceMonthlyReportWizard(models.TransientModel):
	_name = 'ka_hr_attendance.monthly.report.wizard'

	year = fields.Selection([
		(str(num), str(num)) for num in range(datetime.now().year, (datetime.now().year)-5, -1)
	], string="Tahun", required=True)
	month = fields.Selection([
		('01', "Januari"),
		('02', "Pebruari"),
		('03', "Maret"),
		('04', "April"),
		('05', 'Mei'),
		('06', "Juni"),
		('07', "Juli"),
		('08', "Agustus"),
		('09', "September"),
		('10', "Oktober"),
		('11', "Nopember"),
		('12', "Desember"),
	], string="Bulan", required=True)
	company_id = fields.Many2one('res.company', string="Unit/PG", required=True, default=lambda self: self.env.user.company_id)

	@api.multi
	def generate_pdf_report_monthly(self):
		report_obj = self.env['report']
		template = 'ka_hr_attendance.monthly_report_view'
		report = report_obj._get_report_from_name(template)
		domain = {
			'year': self.year,
			'month': self.month,
			'company_id': self.company_id.id
		}

		vals = {
			'ids': self.ids,
			'model': report.model,
			'form': domain
		}

		return report_obj.get_action(self, template, data=vals)

class ReportKaHrAttendanceMonthlyReport(models.AbstractModel):
	_name = 'report.ka_hr_attendance.monthly_report_view'
	_template = 'ka_hr_attendance.monthly_report_view'

	_list_monthname = ["Januari", "Pebruari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "Nopember", "Desember"]

	def _get_active_day(self, month, year, company):
		last_day = calendar.monthrange(int(year), int(month))[1]
		off_day = company.get_off_day()

		active_day = []
		for i in range(last_day):
			date_str = year + '-' + month + '-' + (str(i + 1) if i >= 9 else "0" + (str(i + 1)))

			"""check in holidays_public"""
			holidays_public_count = self.env['ka_hr.holidays.public'].search_count([('tgl_holiday', '=', date_str)])
			if holidays_public_count > 0:
				continue

			date_obj = datetime.strptime(date_str, DATE_FORMAT).date()

			weekday = date_obj.weekday()
			if weekday not in off_day:
				active_day.append(date_str)

		return active_day

	def _get_rekap_data(self, active_day, company):
		datas = []

		active_day_strlist = ", ".join("'" + day + "'" for day in active_day)

		employees = self.env['hr.employee'].search([('pensiun', '=', False), ('company_id', 'child_of', company.id)])
		for employee in employees:
			if not employee.finger_id:
				continue
			count = {
				'attendance': 0,
				'is_telat': 0,
				'is_pulang_cepat': 0,
				'cuti': 0,
				'ijin': 0,
				'dinas': 0,
				'sakit': 0,
				'mangkir': 0,
				'no_check_in': 0,
				'no_check_out': 0,
			}

			for day in active_day:
				sql_attendance = """SELECT check_in, check_out, is_telat, is_pulang_cepat
					FROM hr_attendance
					WHERE employee_id = '%s'
						AND date_in = '%s'""" % (str(employee.id), day)

				self._cr.execute(sql_attendance)
				fetch = self._cr.fetchone()

				if fetch:
					count['attendance'] += 1
					if fetch[0] == None and fetch[1] == None:
						count['mangkir'] += 1
					else:
						if fetch[0] == None:
							count['no_check_in'] += 1
						if fetch[1] == None:
							count['no_check_out'] += 1
					if fetch[2]:
						count['is_telat'] += 1
					if fetch[3]:
						count['is_pulang_cepat'] += 1
				else:
					count['mangkir'] += 1
					# count['no_check_in'] += 1
					# count['no_check_out'] += 1

			sql_holiday = """SELECT c.leave_type
				FROM hr_holidays_lines a
				INNER JOIN hr_holidays b ON a.holiday_id = b.id
				INNER JOIN hr_holidays_status c ON b.holiday_status_id = c.id
				WHERE a.holiday_date IN (%s)
					AND b.employee_id = %s"""

			self._cr.execute(sql_holiday % (active_day_strlist, str(employee.id)))
			fetch_holiday = self._cr.fetchall()

			for leave, in fetch_holiday:
				count[leave] += 1
			
			emp = {
				'employee_id': employee.id,
				'employee_name': employee.name,
				'attendance': "-" if count['attendance'] == 0 else str(count['attendance']),
				'is_telat': "-" if count['is_telat'] == 0 else str(count['is_telat']),
				'is_pulang_cepat': "-" if count['is_pulang_cepat'] == 0 else str(count['is_pulang_cepat']),
				'no_check_in': "-" if count['no_check_in'] == 0 else str(count['no_check_in']),
				'no_check_out': "-" if count['no_check_out'] == 0 else str(count['no_check_out']),
				'cuti': "-" if count['cuti'] == 0 else str(count['cuti']),
				'ijin': "-" if count['ijin'] == 0 else str(count['ijin']),
				'dinas': "-" if count['dinas'] == 0 else str(count['dinas']),
				'sakit': "-" if count['sakit'] == 0 else str(count['sakit']),
				'mangkir': "-" if count['mangkir'] == 0 else str(count['mangkir']),
			}

			datas.append(emp)

		return datas

	def _get_kadiv_sdm(self):
		return self.env.user.company_id.dept_sdm.manager_id.name

	def render_html(self, docids, data=None):
		report_obj = self.env['report']
		model = self._context.get('active_model')
		doc_id = self._context.get('active_id')

		month = data['form']['month']
		year = data['form']['year']
		
		company_id = data['form']['company_id']
		company = self.env['res.company'].browse(company_id)

		active_day = self._get_active_day(month, year, company)

		docs = self._get_rekap_data(active_day, company)
		monthname = self._list_monthname[int(month)-1]
		kadiv_sdm = self._get_kadiv_sdm()

		vals = {
			'docs': docs,
			'monthname': monthname,
			'year': year,
			'day_count': len(active_day),
			'kadiv_sdm': kadiv_sdm,
		}

		return report_obj.render(self._template, values=vals)