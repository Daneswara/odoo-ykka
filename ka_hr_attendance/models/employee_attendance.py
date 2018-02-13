# ----------------------------------------------------------
# Data presensi pegawai
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields, api, exceptions
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from math import modf, floor, ceil
import logging

_logger = logging.getLogger(__name__)

class KaHrEmployeeAttendance(models.Model):
	_inherit = 'hr.attendance'
	_description = "SDM Presensi Pegawai"
	_order = 'id desc'

	"""Override field"""
	check_in = fields.Datetime(string="Check In", default=False, required=False)
	"""end of Override field"""
	
	date_in = fields.Date(compute='_compute_check_in', string="Hari Masuk", store=True)
	is_telat = fields.Boolean(compute='_compute_check_in', string="Terlambat", default=False, store=True)
	is_pulang_cepat = fields.Boolean(compute='_compute_check_out', string="Pulang Cepat", default=False, store=True)
	company_id = fields.Many2one(related='employee_id.company_id', string="Unit/PG")
	have_sp = fields.Boolean()

	# Override
	@api.depends('check_in', 'check_out')
	def _compute_worked_hours(self):
		for attendance in self:
			if attendance.check_in and attendance.check_out:
				delta = datetime.strptime(attendance.check_out, DATETIME_FORMAT) - datetime.strptime(attendance.check_in, DATETIME_FORMAT)
				attendance.worked_hours = delta.total_seconds() / 3600.0

	# Override
	@api.constrains('check_in', 'check_out')
	def _check_validity_check_in_check_out(self):
		"""override _check_validity_check_in_check_out on super(hr.attendance)
		agar tidak bikin error saat input otomatis"""
		pass

	# Override
	@api.constrains('check_in', 'check_out', 'employee_id')
	def _check_validity(self):
		"""override _check_validity on super(hr.attendance)
		agar tidak bikin error saat input otomatis"""
		pass

	def _get_time_in_out(self, group, date_in):
		sql = """SELECT b.time_in, b.time_out FROM hr_attendance_group_shift a 
				INNER JOIN hr_attendance_shift b ON a.shift_id=b.id
				WHERE a.hr_attendance_group_id=%d AND a.date_end >='%s' and a.date_start <='%s'
				LIMIT 1""" %(group.id, date_in, date_in)
		
		self._cr.execute(sql)
		return self._cr.fetchone()

	def _check_telat(self, local_datetime_in):
		group = self.employee_id.hr_attendance_group_id
		"""If not group then raise an exceptions"""
		if not group:
			return
			# raise exceptions.Warning("Grup Shift karyawan belum diisi!")
			# return True

		fetch = self._get_time_in_out(group, self.date_in)
		if not fetch:
			return

		"""dec -> ambil jam_masuk dari fetch untuk membandingkan apakah dia telat atau tidak
		dec menghasilkan tuple(menit, jam)
		shift_time -> jam_masuk yg didapat dikonversikan ke format datetime dengan date_in sebagai tanggalnya"""
		dec = modf(fetch[0])
		shift_as_string = self.date_in + " " + str(int(dec[1])) + ":" + str(int(floor(dec[0]*60))+1) + ":00"
		shift_time = datetime.strptime(shift_as_string, DATETIME_FORMAT)

		return local_datetime_in > shift_time

	def _check_pulang_cepat(self, local_datetime_out):
		group = self.employee_id.hr_attendance_group_id
		"""If not group then raise an exceptions"""
		if not group:
			return
			# raise exceptions.Warning("Grup Shift karyawan belum diisi!")
			# return True

		fetch = self._get_time_in_out(group, self.date_in)
		if not fetch:
			return

		"""dec -> ambil jam_pulang dari fetch untuk membandingkan apakah dia pulang cepat atau tidak
		dec menghasilkan tuple(menit, jam)
		shift_time -> jam_pulang yg didapat dikonversikan ke format datetime dengan date_in sebagai tanggalnya"""
		dec = modf(fetch[1])
		shift_as_string = self.date_in + " " + str(int(dec[1])) + ":" + str(int(ceil(dec[0]*60))-1) + ":00"
		shift_time = datetime.strptime(shift_as_string, DATETIME_FORMAT)

		return local_datetime_out < shift_time

	def _get_jakarta_timezone(self, utc_datetime):
		"""convert datetime timezone from UTC to asia/jakarta"""
		return utc_datetime + timedelta(hours=7)

	@api.depends('check_in')
	def _compute_check_in(self):
		for s in self:
			if s.check_in:
				dt_obj = datetime.strptime(s.check_in, DATETIME_FORMAT)
				dt_local = s._get_jakarta_timezone(dt_obj)
				s.date_in = dt_local.date()
				s.is_telat = s._check_telat(dt_local)

	@api.depends('check_out')
	def _compute_check_out(self):
		for s in self:
			if s.check_out:
				dt_obj = datetime.strptime(s.check_out, DATETIME_FORMAT)
				dt_local = s._get_jakarta_timezone(dt_obj)
				s.is_pulang_cepat = s._check_pulang_cepat(dt_local)

	def check_employee_finger(self):
		datetime_now = self._get_jakarta_timezone(datetime.now())
		date_now = datetime_now.date()
		str_date_now = date_now.strftime(DATE_FORMAT)

		"""cek holiday public pada tanggal ini"""
		holidays_public_count = self.env['ka_hr.holidays.public'].search_count([('tgl_holiday', '=', str_date_now)])
		if holidays_public_count > 0:
			return

		companies = self.env['res.company'].search([])
		for company in companies:
			if company.today_is_off_day():
				continue

			shifts = self.env['hr.attendance.shift'].search([('company_id', '=', company.id)])
			for shift in shifts:
				"""cek dulu apakah jam masuk atau jam keluar
				jika jam masuk, cari pegawai yg belum absen masuk pada hari itu, trus kirim email
				jika jam keluar, cari pegawai yg belum absen pulang pada hari itu, trus kirim email"""
				dec_time_in = modf(shift.time_in)
				str_datetime_in = str_date_now + " " + str(int(dec_time_in[1])) + ":" + str(int(floor(dec_time_in[0]*60))+1) + ":00"
				datetime_in = datetime.strptime(str_datetime_in, DATETIME_FORMAT)
				min_in = datetime_in + timedelta(minutes=30)
				max_in = datetime_in + timedelta(minutes=80)
				
				if datetime_now >= min_in and datetime_now <= max_in:
					"""berarti jam masuk"""
					employees = self.env['hr.employee'].search([
						('pensiun', '=', False),
						('company_id', '=', company.id)
					])
					
					for employee in employees:
						"""klo employee gak punya email, langsung di continue ke employee selanjutnya saja"""
						if not employee.work_email:
							continue

						"""cek apakah employee sedang holiday"""
						employee_holiday_count = self.env['hr.holidays.lines'].search([
							('holiday_id.employee_id', '=', employee.id),
							('holiday_date', '=', str_date_now)
						])

						if employee_holiday_count > 0:
							"""employee sedang holiday, tidak perlu dilanjutkan"""
							continue

						attendance_count = self.env['hr.attendance'].search_count([
							('employee_id', '=', employee.id),
							('date_in', '=', str_date_now)
						])

						if attendance_count > 0:
							"""data ada berarti sudah check_in"""
							continue

						"""kirim email pemberitahuan belum checkin"""
						employee.send_mail_check_in()

					continue
				
				"""check jam keluar"""
				dec_time_out = modf(shift.time_out)
				str_datetime_out = str_date_now + " " + str(int(dec_time_out[1])) + ":" + str(int(ceil(dec_time_out[0]*60))-1) + ":00"
				datetime_out = datetime.strptime(str_datetime_out, DATETIME_FORMAT)
				min_out = datetime_out + timedelta(minutes=30)
				max_out = datetime_out + timedelta(minutes=80)

				if datetime_now >= min_out and datetime_now <= max_out:
					employees = self.env['hr.employee'].search([
						('pensiun', '=', False),
						('company_id', '=', company.id)
					])
					
					for employee in employees:
						"""klo employee gak punya email, langsung di continue ke employee selanjutnya saja"""
						if not employee.work_email:
							continue

						attendances = self.env['hr.attendance'].search([
							('employee_id', '=', employee.id),
							('date_in', '=', str_date_now)
						])

						for attendance in attendances:
							if not attendance.check_out:
								"""belum check out, kirim email"""
								if employee.work_email:
									employee.send_mail_check_out()

	@api.model
	def cron_fingerspot_scan_all(self):
		"""Get fingerspot scan all"""
		_logger.info('========================== Start Download Attendance From SDK ==========================')
		fingerspot_device = self.env['ka_fingerspot.device'].search([])
		for device in fingerspot_device:
			device.action_get_scan_new()
			self._import_data_attendance(device)
		"""End of fingerspot scan all"""
		"""cek untuk employee yg belum melakukan fingerprint"""
		self.check_employee_finger()

	def _import_data_attendance(self, device):
		date_list = [(datetime.now() - timedelta(days=1)).date(), datetime.now().date()]
		scanlog = self.env['ka_fingerspot.scanlog'].search([('date_scan_date', 'in', date_list), ('company_id', 'child_of', device.company_id.id)], order='id asc')
		self.set_data_attendance(scanlog, device.company_id)

	def set_data_attendance(self, scanlog, company):
		if not company.hr_attendance_max_hour:
			return

		for log in scanlog:
			"""jika log tidak ada user_pin id"""
			if not log.user_pin_id.id:
				continue

			employees = self.env['hr.employee'].search([('pensiun', '=', False), ('finger_id', '=', log.user_pin_id.id), ('company_id', 'child_of', company.id)])
			for employee in employees:
				if employee:
					"""ambil data scanlog date_scan_date, cek di attendance apakah sudah ada data yg masuk"""
					attendances = self.search([('employee_id', '=', employee.id)], limit=1) or []
					scan_date_obj = datetime.strptime(log.scan_date, DATETIME_FORMAT)
					checkout = False
					attendance = None

					if len(attendances) > 0:
						attendance = attendances[0]
						"""jika sudah ada bisa pasti tinggal masukkan data attendance check_in atau check_out"""
						"""check selisih jam check_in hari ini vs scan terakhir
						jika > 20 jam maka check_in lagi, jika < 20 jam maka dianggap check_out"""
						datetime_in = datetime.strptime(attendance.check_in, DATETIME_FORMAT)
						selisih = scan_date_obj - datetime_in
						selisih_hours = (selisih.days * 24) + (selisih.seconds / 3600)
						if selisih_hours < company.hr_attendance_max_hour:
							checkout = True

					if checkout and attendance:
						attendance.write({
							'check_out': scan_date_obj
						})
					else:
						self.create({
							'employee_id': employee.id,
							'check_in': scan_date_obj
						})

					self._cr.commit()