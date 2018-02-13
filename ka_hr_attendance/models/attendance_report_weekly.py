# ----------------------------------------------------------
# Data laporan presensi pegawai
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
import base64

class KaHrAttendanceReportWeekly(models.Model):
	_name = 'ka_hr_attendance.report.weekly'
	_report_template = 'ka_hr_attendance.weekly_report_view'
	_order = 'tgl_awal desc'

	tgl_awal = fields.Date(string="Tanggal Awal", required=True, default=fields.Date.today)
	name = fields.Char(string='Nama', compute='_display_name')
	company_id = fields.Many2one('res.company', string="Unit/PG", required=True, default=lambda self: self.env.user.company_id)

	_sql_constraints = [
		('attendance_report_weekly_unique', 'UNIQUE(tgl_awal, company_id)', "Tanggal awal sudah ada, tidak boleh sama!")
	]

	@api.multi
	@api.depends('tgl_awal')
	def _display_name(self):
		for rec in self:
			rec.name = rec.tgl_awal
		
	def _get_jakarta_timezone(self, utc_datetime):
		"""convert datetime timezone from UTC to asia/jakarta"""
		return utc_datetime + timedelta(hours=7)

	def generate_pdf_report(self):
		report_obj = self.env['report']
		report = report_obj._get_report_from_name(self._report_template)
		domain = {
			'tgl_awal': self.tgl_awal,
			'company_id': self.company_id.id,
		}

		values = {
			'ids': self.ids,
			'model': report.model,
			'form': domain
		}

		# generate_pdf_report() digunakan untuk passing data ke ReportKaHrActivityPresensiWeekly(models.abstractModel)
		# jika return report get_action maka mengarah ke render_html di ReportKaHrActivityPresensiWeekly(models.abstractModel)
		return report_obj.get_action(self, self._report_template, data=values)

	def _set_attachment(self, pdf):
		attachments = self.env['ir.attachment'].search([
			('res_model', '=', self._name), ('res_id', '=', self.id)
		], limit=1)

		attachment_name = 'Presensi_Mingguan_%s_%s' % (self.company_id.name, self.tgl_awal)
		attachment = None
		if len(attachments) > 0:
			attachment = attachments[0]
			attachment.write({
				'name': attachment_name,
				'datas': base64.encodestring(pdf),
				'datas_fname': attachment_name + ".pdf",
				'store_fname': attachment_name,
			})

			self._cr.commit()
		else:
			attachment = self.env['ir.attachment'].create({
				'name': attachment_name,
				'type': 'binary',
				'datas': base64.encodestring(pdf),
				'datas_fname': attachment_name + ".pdf",
				'store_fname': attachment_name,
				'res_model': self._name,
				'res_id': self.id,
				'mimetype': 'application/x-pdf',
			})
			self._cr.commit()

	def get_default_pdf(self):
		pdf = self.env['report'].get_pdf([self.id], self._report_template, data=self.generate_pdf_report())
		self._set_attachment(pdf)

	def cron_weekly_report_mail(self):
		datetime_now = self._get_jakarta_timezone(datetime.now())
		idx = datetime_now.weekday()

		companies = self.env['res.company'].search([])
		for company in companies:
			"""Jika belum disetting maka di continue saja"""
			if not company.hr_attendance_weekly_report_send or not company.email_group:
				continue

			"""jika indexnya tidak sama dengan setting hari kirim report maka di continue"""
			if idx != company.hr_attendance_weekly_report_send:
				continue

			selisih = 0
			if idx >= 4:
				"""hari yg dipilih atau sesudahnya maka diambil hari senin -> minggu ini"""
				selisih = company.hr_attendance_weekly_report_send
			else:
				"""jika sebelum hari yg dipilih maka diambil muali hari senin -> minggu sebelumnya"""
				selisih = idx + 7

			tgl_awal_report = datetime_now - timedelta(days=selisih)

			str_tgl_awal_report = tgl_awal_report.strftime(DATE_FORMAT)
			reports = self.search([
				('tgl_awal', '=', str_tgl_awal_report),
				('company_id', '=', company.id)
			], limit=1)
			
			obj = None
			if len(reports) > 0:
				obj = reports[0]
			else:
				obj = self.create({
					'tgl_awal': str_tgl_awal_report,
					'company_id': company.id,
				})
				self._cr.commit()
				
			obj.get_default_pdf()
			obj.send_mail_report()

		self.check_employee_attendance_weekly(idx=idx, companies=companies)

	def check_employee_attendance_weekly(self, idx=None, companies=None):
		if not idx:
			datetime_now = self._get_jakarta_timezone(datetime.now())
			idx = datetime_now.weekday()

		if not companies:
			companies = self.env['res.company'].search([])
		
		for company in companies:
			if idx != company.hr_attendance_weekly_check:
				continue
			
			employees = self.env['hr.employee'].search([
				('pensiun', '=', False),
				('company_id', '=', company.id),
			])

			for employee in employees:
				"""cek telat 2 hari dalam 1 minggu"""
				sql_weekly = """SELECT id, date_in FROM hr_attendance
					WHERE employee_id = {}
						AND date_part('week', date_in) = date_part('week', CURRENT_DATE)
						AND date_part('year', date_in) = date_part('year', CURRENT_DATE)
						AND is_telat = {}
						AND have_sp = {};""".format(employee.id, True, False)

				self._cr.execute(sql_weekly)
				fetch = self._cr.fetchall()
				if len(fetch) >= company.hr_attendance_sp_late_weekly:
					list_date = [datetime.strptime(f[1], DATE_FORMAT).strftime('%d-%m-%Y') for f in fetch]
					str_date = ", ".join(list_date)
					aid = ", ".join([str(f[0]) for f in fetch])
					sql_update = """UPDATE hr_attendance
						SET have_sp = {}
						WHERE id in ({})""".format(True, aid)

					self._cr.execute(sql_update)
					self.env['hr.employee.sp'].create_sp_telat_weekly(employee.id, str_date)
					self._cr.commit()

				sql_monthly = """SELECT id, date_in FROM hr_attendance
					WHERE employee_id = {}
						AND date_part('month', date_in) = date_part('month', CURRENT_DATE)
						AND date_part('year', date_in) = date_part('year', CURRENT_DATE)
						AND is_telat = {}
						AND have_sp = {};""".format(employee.id, True, False)

				self._cr.execute(sql_monthly)
				fetch = self._cr.fetchall()
				if len(fetch) >= company.hr_attendance_sp_late_monthly:
					list_date = [datetime.strptime(f[1], DATE_FORMAT).strftime('%d-%m-%Y') for f in fetch]
					str_date = ", ".join(list_date)
					aid = ", ".join([str(f[0]) for f in fetch])
					sql_update = """UPDATE hr_attendance
						SET have_sp = {}
						WHERE id in ({})""".format(True, aid)

					self._cr.execute(sql_update)
					self.env['hr.employee.sp'].create_sp_telat_weekly(employee.id, str_date)
					self._cr.commit()

	def send_mail_report(self):
		template = self.env.ref('ka_hr_attendance.template_mail_weekly_report')
		mail = self.env['mail.template'].browse(template.id)
		"""update data attachment_ids"""
		mail.email_to = self.company_id.email_group
		mail.attachment_ids = self.env['ir.attachment'].search([
			('res_model', '=', self._name),
			('res_id', '=', self.id)
		])
		self._cr.commit()
		mail.send_mail(self.id, force_send=True)
		"""setelah diupdate di kosongi lagi"""
		mail.email_to = None
		mail.attachment_ids = None
		self._cr.commit()

class ReportKaHrAttendanceWeeklyReport(models.AbstractModel):
	_name = 'report.ka_hr_attendance.weekly_report_view'
	_template = 'ka_hr_attendance.weekly_report_view'

	_list_dayname = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
	_list_monthname = ["Januari", "Pebruari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "Nopember", "Desember"]

	def _get_jakarta_timezone(self, utc_datetime):
		"""convert datetime timezone from UTC to asia/jakarta"""
		return utc_datetime + timedelta(hours=7)

	def _get_presensi_data(self, tgl_list, company_id):
		datas = []

		"""ambil semua data employee yg aktif berdasarkan company_id"""
		employees = self.env['hr.employee'].search([('pensiun', '=', False), ('company_id', 'child_of', company_id)])

		for employee in employees:
			if not employee.finger_id:
				continue
			emp = {
				'employee_id': employee.id,
				'employee_name': employee.name,
				'activity': []
			}

			for tgl in tgl_list:
				act = {}
				tgl_str = tgl.strftime(DATE_FORMAT)

				"""cek attendance pada tanngal ini & employee ini"""
				attendances = self.env['hr.attendance'].search([
					('employee_id', '=', employee.id),
					('date_in', '=', tgl_str),
				], limit=1)

				if len(attendances) > 0:
					attendance = attendances[0]
					if attendance.check_in:
						ci = datetime.strptime(attendance.check_in, DATETIME_FORMAT)
						ci_local = self._get_jakarta_timezone(ci)
						ci_time = ci_local.time()
						act['check_in'] = ci_time.strftime('%H:%M')
					else:
						act['check_in'] = "-"
								
					if attendance.check_out:
						co = datetime.strptime(attendance.check_out, DATETIME_FORMAT)
						co_local = self._get_jakarta_timezone(co)
						co_time = co_local.time()
						act['check_out'] = co_time.strftime('%H:%M')
					else:
						act['check_out'] = "-"

					act['is_telat'] = attendance.is_telat
					act['is_pulang_cepat'] = attendance.is_pulang_cepat
					act['holiday_status'] = "-"
				else:
					act['check_in'] = "-"
					act['check_out'] = "-"
					act['is_telat'] = False
					act['is_pulang_cepat'] = False

					"""cek holiday public pada tanggal ini"""
					holidays_public_count = self.env['ka_hr.holidays.public'].search_count([('tgl_holiday', '=', tgl_str)])

					if holidays_public_count > 0:
						act['holiday_status'] = "Libur"
					else:
						"""cek holidays pada tanggal ini & employee ini"""
						holidays = self.env['hr.holidays.lines'].search([
							('holiday_id.employee_id', '=', employee.id),
							('holiday_date', '=', tgl_str)
						], limit=1)

						if len(holidays) > 0:
							holiday = holidays[0]
							act['holiday_status'] = holiday.holiday_id.holiday_status_id.code
						else:
							act['holiday_status'] = "-"

				emp['activity'].append(act)

			datas.append(emp)

		return datas

	def _get_date_list(self, tgl_list):
		date_list = []
		for tgl in tgl_list:
			idx = tgl.weekday()
			format_tgl = tgl.strftime('%d/%m/%Y')
			date_list.append(self._list_dayname[idx] + ", " + format_tgl)

		return date_list

	def _get_monthname(self, tgl):
		idx = tgl.month-1
		return self._list_monthname[idx]

	def _get_kadiv_sdm(self):
		return self.env.user.company_id.dept_sdm.manager_id.name

	@api.multi
	def render_html(self, docids, data=None):
		report_obj = self.env['report']
		model = self._context.get('active_model') or data['data']['model']
		doc_id = self._context.get('active_id') or data['data']['ids']
		presensi = self.env[model].browse(doc_id)
		company_id = None
		if data.has_key('form'):
			company_id = data['form']['company_id']
		else:
			company_id = data['data']['form']['company_id']

		tgl_awal = datetime.strptime(presensi.tgl_awal, DATE_FORMAT).date()
		tgl_list = [tgl_awal + timedelta(days=i) for i in range(5)]
		
		date_list = self._get_date_list(tgl_list)
		monthname = self._get_monthname(tgl_awal)
		year = tgl_awal.year
		docs = self._get_presensi_data(tgl_list, company_id)
		strdate_awal = tgl_awal.strftime('%d/%m/%Y')
		strdate_akhir = tgl_list[4].strftime('%d/%m/%Y')
		kadiv_sdm = self._get_kadiv_sdm()

		vals = {
			'docs': docs,
			'monthname': monthname,
			'year': year,
			'strdate_awal': strdate_awal,
			'strdate_akhir': strdate_akhir,
			'date_list': date_list,
			'kadiv_sdm': kadiv_sdm,
		}

		return report_obj.render(self._template, values=vals)