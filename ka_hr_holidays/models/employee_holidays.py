# ----------------------------------------------------------
# Data absensi pegawai, baik cuti, ijin atau bolos
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields, api
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.exceptions import UserError, ValidationError

class KaHrEmployeeHolidays(models.Model):
	_inherit = 'hr.holidays'
	_description = "SDM Absensi Pegawai"
	_order = 'id desc'

	NO_CONFIG_DINAS_MESSAGE = "Nomor dinas belum diatur! Hubungi administrator untuk melanjutkan!"

	_ADD_PREVIOUS_SISA = "Tambahan sisa cuti pada periode sebelumny sebanyak {} hari"
	_ALLOCATION_YEARLY_NAME = "Alokasi jatah cuti tahunan"
	_ALLOCATION_BIG_NAME = "Alokasi jatah cuti besar"
	_FLUSH_YEARLY_NAME = "Penghapusan sisa cuti tahunan"
	_FLUSH_BIG_NAME = "Penghapusan sisa cuti besar"
	_INHALDAGEN_NAME = "Inhaldagen dinas"
	_INHALDAGEN_NOTES = "Kompensasi dinas dari Surat Tugas No. {}"
	_FLUSH_INHALDAGEN_NAME = "Penghapusan inhaldagen yang kadaluwarsa"
	_FLUSH_HUTANG_CUTI = "Penghapusan karena hutang cuti"

	def _default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	"""override default fields"""
	holiday_status_id = fields.Many2one("hr.holidays.status", string="Leave Type", required=False, readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})

	state = fields.Selection([
		('draft', 'To Submit'),
		('cancel', 'Cancelled'),
		('confirm', 'To Approve'),
		('refuse', 'Refused'),
		('validate1', 'Second Approval'),
		('validate', 'Approved')
	], string='Status', readonly=True, track_visibility='onchange', copy=False, default='draft',
		help="The status is set to 'To Submit', when a holiday request is created." +
		"\nThe status is 'To Approve', when holiday request is confirmed by user." +
		"\nThe status is 'Refused', when holiday request is refused by manager." +
		"\nThe status is 'Approved', when holiday request is approved by manager.")

	employee_id = fields.Many2one('hr.employee', string='Employee',
		index=True, required=True, domain=[('pensiun', '=', False)], default=_default_employee)
	date_from = fields.Date(string="Tanggal Awal", readonly=True, index=True, copy=False,
		states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
	date_to = fields.Date('End Date', readonly=True, copy=False,
		states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
	date_request = fields.Date(string="Tanggal", required=True, default=fields.Date.today)
	company_id = fields.Many2one(related='employee_id.company_id', string="Unit/PG", required=True,
		readonly=True)
	type = fields.Selection([
		('remove', 'Leave Request'),
		('add', 'Allocation Request'),
		('flush', 'Flush Active Add Request'),
	], string='Request Type', required=True, readonly=True, index=True, default='remove',
		states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
		help="Choose 'Leave Request' if someone wants to take an off-day.\nChoose 'Allocation Request' if you want to increase the number of leaves available for someone")
	"""end of override"""

	holiday_address = fields.Text(string="Alamat")
	is_active = fields.Boolean(string="Active") # hanya untuk menandai cuti yg tipe 'add' sebagai referensi cuti yg sedang aktif yg akan diambil nantinya

	employee_manager_id = fields.Many2one(related='employee_id.parent_id')
	manager_departement_id = fields.Many2one(related='employee_manager_id.department_id')
	holiday_status_leave_type = fields.Selection(related='holiday_status_id.leave_type', readonly=True)
	holiday_status_daily_type = fields.Boolean(related='holiday_status_id.is_daily_type', readonly=True)
	# holiday_status_parent = fields.Boolean(related='holiday_status_id.is_need_parent', readonly=True)
	employee_user_id = fields.Many2one(related='employee_id.user_id') # helper agar yg tampil nanti = uid

	holiday_status_help = fields.Selection([
		('cuti', "Cuti"),
		('ijin', "Ijin"),
		('dinas', "Dinas"),
		('sakit', "Sakit"),
		('mangkir', "Mangkir"),
		# ('flush', "Flush"),
	], default='cuti')

	nomor_dinas = fields.Char(string="No. Surat", size=32, readonly=True, default='/')
	
	date_start = fields.Date(string="Tanggal Mulai",
		help="Tanggal mulai berlaku cuti. Khusus untuk 'type' = 'add'")
	date_exp = fields.Date(string="Tanggal Kadaluwarsa",
		help="Tanggal kadaluwarsa cuti. Khusus untuk 'type' = 'add'")
	flush_reference_id = fields.Many2one('hr.holidays', string="Yang Dihapus",
		help="Referensi untuk flush sisa cuti / inhaldagen ataupun hutang cuti (cuti yang di flush). Khusus untuk 'type' = 'flush'")
	holiday_group_id = fields.Many2one('ka_hr.holidays.group', string="Ref. Cuti Bersama", ondelete='cascade',
		help="Hanya sebagai referensi, jika cutinya cuti bersama")

	cuti_line_ids = fields.One2many('hr.holidays.lines', 'holiday_id', string="Detail Cuti")
	dinas_line_ids = fields.One2many('hr.holidays.lines', 'holiday_id', string="Detail Dinas")
	absensi_line_ids = fields.One2many('hr.holidays.lines', 'holiday_id', string="Detail Absensi")
	remove_line_ids = fields.One2many('hr.holidays.lines', 'cuti_reference_id', string="Detail Pengambilan Cuti")

	is_inhaldagen = fields.Boolean(string="Inhaldagen", readonly=True,
		help="Apakah alokasi untuk inhaldagen?")
	dinas_reference_id = fields.Many2one('hr.holidays', string="Referensi Dinas",
		help="Hanya sebagai referensi dinas, cuti yang dapat inhaldagen")

	kompensasi_hutang_line_ids = fields.One2many('hr.holidays.kompensasi.hutang.lines', 'kompensasi_reference_id',
		string="Detail Kompensasi Hutang")
	count_kompensasi = fields.Integer(compute='_compute_kompensasi')

	# untuk keperluan mail template
	def get_local_date_start_exp(self):
		date_start_obj = datetime.strptime(self.date_start, DATE_FORMAT)
		date_exp_obj = datetime.strptime(self.date_exp, DATE_FORMAT)
		return '{0} - {1}'.format(date_start_obj.strftime("%d-%m-%Y"), date_exp_obj.strftime("%d-%m-%Y"))

	# @override
	@api.multi
	def name_get(self):
		res = []
		for s in self:
			name = ''
			if s.type == 'remove':
				name = '{0} - {1} {2} {3}'.format(s.employee_id.name, s.holiday_status_id.name,
					s.number_of_days_temp, s.holiday_status_id.satuan)
			elif s.type == 'add':
				name = '{0} - Alokasi {1}'.format(s.employee_id.name, s.holiday_status_id.name)
			else:
				name = '{0} - Penghapusan Cuti'.format(s.employee_id.name)

			res.append((s.id, name))

		return res

	# @override
	@api.model
	def name_search(self, name='', args=None, operator='ilike', limit=80):
		if not args:
			args = []

		if name:
			record = self.search([
				'|', ('employee_id', operator, name), ('number_of_days_temp', operator, name)
			] + args, limit=limit)
		else:
			record = self.search(args, limit=limit)

		return record.name_get()

	@api.multi
	def _compute_kompensasi(self):
		for holiday in self:
			holiday.count_kompensasi = len(holiday.kompensasi_hutang_line_ids)

	def get_nomor_dinas(self, company_id):
		sequences = self.env['ir.sequence'].search([
			('code', 'like', 'employee.surat.tugas%'),
			('company_id', '=', company_id)
		], limit=1)

		if len(sequences) > 0:
			sequence = sequences[0]
			return sequence.next_by_id()

		return None

	def get_employee_job_level(self):
		"""untuk mencari level job employee
		sementara menggunakan raw sql query karena masalah hak akses user""" 
		sql = """SELECT b.level FROM hr_employee a
			INNER JOIN hr_job b ON a.job_id = b.id
			WHERE a.id = %s""" % (self.employee_id.id,)

		self._cr.execute(sql)
		fetch = self._cr.fetchone()
		return fetch[0]

	def get_employee_job_name(self):
		"""untuk mencari nama job employee
		sementara menggunakan raw sql query karena masalah hak akses user"""
		sql = """SELECT b.name FROM hr_employee a
			INNER JOIN hr_job b ON a.job_id = b.id
			WHERE a.id = %s""" % (self.employee_id.id,)

		self._cr.execute(sql)
		fetch = self._cr.fetchone()
		return fetch[0]

	# Override
	def _onchange_date_from(self):
		pass

	# Override
	def _onchange_date_to(self):
		pass

	# def _get_parent(self, employee_id, holiday_status_id):
	# 	parent = self.search([
	# 		('employee_id', '=', employee_id),
	# 		('is_active', '=', True),
	# 		('type', '=', 'add'),
	# 		('holiday_status_id', '=', holiday_status_id)
	# 	], limit=1, order='id desc') or []
	# 	return parent

	# Override
	@api.model
	def create(self, vals):
		if not vals.has_key('company_id'):
			employee = self.env['hr.employee'].browse(vals['employee_id'])
			vals['company_id'] = employee.company_id.id

		if vals.has_key('holiday_status_help') and vals['holiday_status_help'] == 'dinas':
			no = self.get_nomor_dinas(vals['company_id'])
			if no:
				vals['nomor_dinas'] = no
			else:
				raise ValidationError(self.NO_CONFIG_DINAS_MESSAGE)
		
		return super(KaHrEmployeeHolidays, self).create(vals)

	# # Override
	# @api.multi
	# def write(self, vals):
	# 	if vals.has_key('employee_id') or vals.has_key('holiday_status_id'):
	# 		employee_id = self.employee_id.id
	# 		holiday_status_id = self.holiday_status_id.id
	# 		if vals.has_key('employee_id') and vals['employee_id'] != False:
	# 			employee_id = vals['employee_id']
	# 		if vals.has_key('holiday_status_id') and vals['holiday_status_id'] != False:
	# 			holiday_status_id = vals['holiday_status_id']

	# 	return super(KaHrEmployeeHolidays, self).write(vals)

	# @api.onchange('employee_id', 'holiday_status_id')
	# def _onchange_parent(self):
	# 	if self.employee_id and self.holiday_status_id:
	# 		parent = self._get_parent(self.employee_id.id, self.holiday_status_id.id)
	# 		if len(parent) > 0: 
	# 			self.parent_id = parent[0].id
	# 		else:
	# 			self.parent_id = False
	# 	else:
	# 		self.parent_id = False

	@api.onchange('holiday_status_id')
	def _onchange_holiday_status(self):
		self.date_to = False
		self.date_from = False
		self.number_of_days_temp = 0.00

	@api.onchange('date_from')
	def _onchange_date_from(self):
		if self.date_from and not self.holiday_status_daily_type:
			alokasi = self.holiday_status_id.jumlah
			if self.holiday_status_id.satuan == 'bulan':
				alokasi *= 30

			date_from_obj = datetime.strptime(self.date_from, DATE_FORMAT)
			self.date_to = date_from_obj + timedelta(days=(alokasi-1))

	@api.onchange('date_from', 'date_to')
	def _onchange_date(self):
		if self.date_from and self.date_to:
			self.number_of_days_temp = len(self._get_date_list())
		else:
			self.number_of_days_temp = 0.00

	def _get_date_list(self):
		date_awal = datetime.strptime(self.date_from, DATE_FORMAT).date()
		date_akhir = datetime.strptime(self.date_to, DATE_FORMAT).date()

		off_day = self.company_id.get_off_day()
		selisih = (date_akhir - date_awal).days

		date_list = []
		for i in range(selisih + 1):
			date_idx = date_awal + timedelta(days=i)
			str_date = date_idx.strftime(DATE_FORMAT)

			if self.holiday_status_daily_type:
				"""Tipe pengambilan cuti adalah harian"""
				"""check date in holiday"""
				holiday = self.env['ka_hr.holidays.public'].search_count([
					('tgl_holiday', '=', str_date),
					('company_id', '=', self.company_id.id),
				])
				if holiday > 0:
					continue
				
				"""check date is sabtu / minggu, jika bukan sabtu atau minggu
					& holiday dan juga bukan dinas, maka diappend ke date_list"""
				idx = date_idx.weekday()
				if idx in off_day and self.holiday_status_help != 'dinas':
					continue

			date_list.append(str_date)

		return date_list

	# Override
	@api.multi
	def action_confirm(self):
		if self.filtered(lambda holiday: holiday.state != 'draft'):
			raise UserError(_('Leave request must be in Draft state ("To Submit") in order to confirm it.'))

		for s in self:
			s.state = 'confirm'
			if not s.employee_manager_id.work_email:
				continue

			if s.type == 'remove' and s.holiday_status_help == 'cuti':
				template = self.env.ref('ka_hr_holidays.template_mail_cuti_approval')
				self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)

	# static
	def get_active_inhaldagen(self, employee, date_obj=None):
		"""untuk cari inhaldagen yang aktif"""
		company = employee.company_id
		if not company.check_requirement():
			raise ValidationError(company.NO_CONFIG_MESSAGE)
			
		company = employee.company_id
		inhaldagen_item_id = company.hr_holidays_inhaldagen_item.id
		if date_obj:
			str_date = ''
			if isinstance(date_obj, datetime):
				str_date = date_obj.strftime(DATE_FORMAT)
			else:
				str_date = date_obj

			return self.search([
				('holiday_status_id', '=', inhaldagen_item_id),
				('employee_id', '=', employee.id),
				('date_start', '<=', str_date),
				('date_exp', '>', str_date),
				('is_active', '=', True),
				('state', '=', 'validate')
			], limit=1, order='date_start asc')
		else:
			return self.search([
				('holiday_status_id', '=', inhaldagen_item_id),
				('employee_id', '=', employee.id),
				('is_active', '=', True),
				('state', '=', 'validate')
			], limit=1, order='date_start asc')

	# static
	def get_sisa_inhaldagen(self, employee):
		"""untuk cari sisa / jumlah inhaldagen dari seorang pegawai"""
		company = employee.company_id
		if not company.check_requirement():
			raise ValidationError(company.NO_CONFIG_MESSAGE)

		return self.search_count([
			('employee_id', '=', employee.id),
			('holiday_status_id', '=', company.hr_holidays_inhaldagen_item.id),
			('type', '=', 'add'),
			('is_active', '=', True),
			('state', '=', 'validate')
		])

	# static
	def get_active_holidays(self, employee, holiday_item):
		"""untuk cari cuti tahunan / besar yang sedang aktif, tergantung dari item yg dipassing"""
		company = employee.company_id
		if not company.check_requirement():
			raise ValidationError(company.NO_CONFIG_MESSAGE)

		return self.search([
			('employee_id', '=', employee.id),
			('holiday_status_id', '=', holiday_item.id),
			('type', '=', 'add'),
			('is_active', '=', True),
			('state', '=', 'validate'),
		], limit=1, order='id desc')

	# static
	def get_sisa_holidays(self, employee, holiday_item):
		"""untuk cari sisa cuti tahunan / besar, tergantung dari item yg dipassing"""
		company = employee.company_id
		if not company.check_requirement():
			raise ValidationError(company.NO_CONFIG_MESSAGE)

		holidays = self.get_active_holidays(employee, holiday_item)
		if len(holidays) > 0:
			lines_count = self.env['hr.holidays.lines'].search_count([
				'|',
				'&', ('cuti_reference_id', '=', holidays[0].id), ('is_hutang', '=', False),
				'&', ('cuti_reference_id', '=', holidays[0].id), '&', ('is_hutang', '=', True), ('kompensasi_reference_id', '=', False)
			])
			return {'holiday': holidays[0], 'sisa': holidays[0].number_of_days_temp - lines_count}

		return {'holiday': None, 'sisa': 0}

	# static
	def create_default_yearly_holidays(self, employee):
		"""untuk membuat nilai awal cuti tahunan, nilai alokasi diisi 0, untuk keperluan pemotongan cuti bersama"""
		company = employee.company_id
		yearly_item = company.hr_holidays_yearly_item
		
		if not yearly_item:
			return

		vals = {
			'name': self._ALLOCATION_YEARLY_NAME,
			'holiday_status_id': yearly_item.id,
			'is_active': True,
			'type': 'add',
			'number_of_days_temp': 0,
			'employee_id': employee.id,
			'holiday_status_help': 'cuti',
			'state': 'confirm',
		}

		if employee.tgl_masuk:
			datetime_obj = self._get_jakarta_timezone(datetime.now())
			today = datetime_obj.date()
			str_today = today.strftime('%m-%d')

			last_datetime_obj = datetime.strptime(employee.tgl_masuk, DATE_FORMAT) - timedelta(days=1)
			
			date_exp = '{}-{}-{}'.format((datetime_obj.year + company.hr_holidays_yearly_periodic),
				last_datetime_obj.month, last_datetime_obj.day)
		
			vals['date_start'] = today.strftime(DATE_FORMAT)
			vals['date_exp'] = date_exp

		default_holiday = self.create(vals)
		default_holiday.sudo().action_validate()
		return default_holiday

	# static
	def _get_cuti_reference(self, employee, date_obj):
		company = employee.company_id
		is_hutang = True
		cuti_reference_id = None

		"""set default cuti_reference_id"""
		yearly_holiday = self.get_sisa_holidays(employee, company.hr_holidays_yearly_item)

		"""cari holiday 'add' yang aktif, jika tidak ada maka buat default,
		karena parent_id harus ada"""
		if yearly_holiday['holiday']:
			cuti_reference_id = yearly_holiday['holiday'].id
		else:
			default_holiday = self.create_default_yearly_holidays(employee)
			cuti_reference_id = default_holiday.id

		inhaldagen =  self.get_active_inhaldagen(employee, date_obj)
		if len(inhaldagen) > 0:
			cuti_reference_id = inhaldagen.id
			"""non aktifkan inhaldagen jika sudah pernah digunakan"""
			is_hutang = False
			inhaldagen.is_active = False
		else:
			if yearly_holiday['sisa'] <= 0:
				big_holiday = self.get_sisa_holidays(employee, company.hr_holidays_big_item)
				if big_holiday['holiday']:
					cuti_reference_id = big_holiday['holiday'].id
					is_hutang = False
			else:
				is_hutang = False

		return {'cuti_reference_id': cuti_reference_id, 'is_hutang': is_hutang}

	# Override
	@api.multi
	def action_validate(self, is_cuti_bersama=False):
		for s in self:
			if not s.company_id.check_requirement():
				raise ValidationError(company.NO_CONFIG_MESSAGE)
		
		"""after validate, create holidays lines"""
		super(KaHrEmployeeHolidays, self).action_validate()
		for s in self:
			if s.type == 'remove' and s.holiday_status_daily_type:
				date_list = s._get_date_list()
				for dl in date_list:
					vals = {
						'holiday_id': s.id,
						'holiday_date': dl,
						'company_id': s.company_id.id,
						'cuti_reference_id': None,
					}

					if s.holiday_status_help == 'cuti':
						cuti_reference = self._get_cuti_reference(s.employee_id, dl)
						if cuti_reference['cuti_reference_id']:
							vals['cuti_reference_id'] = cuti_reference['cuti_reference_id']
							vals['is_hutang'] = cuti_reference['is_hutang']
						
						if not is_cuti_bersama:
							"""tambahkan kirim email untuk pegawai"""
							template = self.env.ref('ka_hr_holidays.template_mail_cuti_approved')
							self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)

					s.env['hr.holidays.lines'].create(vals)

	# static
	def flush_holidays(self, flush_reference, flush_name, qty, line_hutang=None):
		employee = flush_reference.employee_id
		company = employee.company_id
		vals = {
			'name': flush_name,
			'type': 'flush',
			'number_of_days_temp': qty,
			'flush_reference_id': flush_reference.id,
			'employee_id': employee.id,
			'state': 'confirm',
		}

		flush = self.create(vals)
		flush.sudo().action_validate()

		if line_hutang:
			for hutang in line_hutang:
				self.env['hr.holidays.kompensasi.hutang.lines'].create({
					'kompensasi_reference_id': flush.id,
					'hutang_reference_id': hutang.holiday_id.id
				})

	# Override
	@api.multi
	def action_refuse(self):
		"""unlink all related cuti_line_ids when refused after validate"""
		super(KaHrEmployeeHolidays, self).action_refuse()
		for s in self:
			if s.type == 'remove':
				for line in s.cuti_line_ids:
					line.unlink()

				if s.holiday_status_help == 'cuti':
					template = self.env.ref('ka_hr_holidays.template_mail_cuti_refused')
					self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)

	def _get_terbilang(self, angka):
		kata = ["se", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan"]
		tambahan = ["belas", "puluh", "ratus"]

		terbilang = ""

		ratusan = angka / 100
		if ratusan >= 1:
			if ratusan == 1:
				terbilang += kata[0] + tambahan[2]
			else:
				terbilang += kata[ratusan] + " " + tambahan[2]
			terbilang += " "

		puluhan = (angka % 100) / 10
		if puluhan > 1:
			terbilang += kata[puluhan] + " " + tambahan[1] + " "

		satuan = (angka % 100) % 10
		if satuan >= 1:
			if puluhan == 1:
				if satuan == 1:
					terbilang += kata[0]
				else:
					terbilang += kata[satuan] + " "
				terbilang += tambahan[0]
			else:
				terbilang += kata[satuan]

		return terbilang

	def _get_jakarta_timezone(self, utc_datetime):
		"""convert datetime timezone from UTC to asia/jakarta"""
		return utc_datetime + timedelta(hours=7)

	def _check_holidays_allocation(self):
		"""Untuk cek alokasi cuti karyawan, konsepnya ada cron mengecek harian employee,
		yg tanggal masuk sama dengan tanggal hari ini, jika sama tinggal tambahkan alokasi cuti tahunan & cuti besar"""
		datetime_obj = self._get_jakarta_timezone(datetime.now())
		# datetime_obj = datetime.strptime('2017-10-20', DATE_FORMAT)
		today = datetime_obj.date()
		str_today = today.strftime('%m-%d')
		
		"""kabisat dihitung tiap tanggal 1 maret, biar gak kisruh"""
		if str_today != '02-29':
			last_datetime_obj = today - timedelta(days=1)
	
			employee_obj = self.env['hr.employee']
			employees = []
			if str_today == '03-01':
				employees = employee_obj.search([('pensiun', '=', False), '|', ('tgl_masuk', 'like', ('%'+str_today)), ('tgl_masuk', 'like', '%02-29')])
			else:
				employees = employee_obj.search([('tgl_masuk', 'like', ('%'+str_today)), ('pensiun', '=', False)])

			for employee in employees:
				company = employee.company_id
				if not company.check_requirement():
					continue

				max_sisa_yearly = company.hr_holidays_max_sisa_yearly
				sisa_yearly = 0
				notes = None

				"""cek cuti tahunan, jika ada di flush"""
				holiday_yearly = self.get_sisa_holidays(employee, company.hr_holidays_yearly_item)

				if holiday_yearly.has_key('holiday') and holiday_yearly['holiday']:
					holiday = holiday_yearly['holiday']
					sisa = holiday_yearly['sisa']

					if sisa > max_sisa_yearly:
						sisa_yearly = max_sisa_yearly
					else:
						sisa_yearly = sisa

					if sisa > 0:
						"""jika ada sisa buat cuti yg type 'flush' untuk menghanguskan cuti"""
						self.flush_holidays(flush_reference=holiday, flush_name=self._FLUSH_YEARLY_NAME,
							qty=sisa)

					"""set holiday active=False"""
					holiday.is_active = False

				tgl_acuan_obj = datetime.strptime(employee.tgl_masuk, DATE_FORMAT).date()
				periode = (today.year - tgl_acuan_obj.year) % company.hr_holidays_big_periodic
				
				if periode == 0:
					"""berarti diberikan cuti besar"""
					alokasi = company.hr_holidays_big_item.jumlah

					if company.hr_holidays_big_item.satuan == 'bulan':
						"""Jika bulan maka dikonversi ke hari, karena pengambilan harian"""
						alokasi *= 30

					is_punya_hutang = False
					sisa_big = 0

					holiday_big = self.get_sisa_holidays(employee, company.hr_holidays_big_item)
					if holiday_big.has_key('holiday') and holiday_big['holiday']:
						holiday = holiday_big['holiday']
						sisa_big = holiday_big['sisa']
						max_sisa_big = company.hr_holidays_max_sisa_big
						
						if sisa_big < 0:
							is_punya_hutang = True
						else:
							if sisa > max_sisa_big:
								alokasi += max_sisa_big
							else:
								alokasi += sisa_big

						if sisa_big > 0:
							if sisa_big <= max_sisa_big:
								notes = self._ADD_PREVIOUS_SISA.format({sisa_big})

							self.flush_holidays(flush_reference=holiday, flush_name=self._FLUSH_BIG_NAME,
								qty=sisa_big)

						"""set holiday active=False"""
						holiday.is_active = False


					date_exp = '{0}-{1}-{2}'.format((last_datetime_obj.year + company.hr_holidays_big_periodic),
						last_datetime_obj.month, last_datetime_obj.day)

					"""tambahkan alokasi cuti baru"""
					allocation_vals = {
						'name': self._ALLOCATION_BIG_NAME,
						'holiday_status_id': company.hr_holidays_big_item.id,
						'type': 'add',
						'is_active': True,
						'number_of_days_temp': alokasi,
						'employee_id': employee.id,
						'state': 'confirm',
						'holiday_status_help': 'cuti',
						'date_start': today.strftime(DATE_FORMAT),
						'date_exp': date_exp,
						'notes': notes,
					}

					new_allocation = self.create(allocation_vals)
					new_allocation.sudo().action_validate()

					template = self.env.ref('ka_hr_holidays.template_mail_cuti_allocation')
					self.env['mail.template'].browse(template.id).send_mail(new_allocation.id)

					if is_punya_hutang:
						self.flush_holidays(flush_reference=new_allocation, flush_name=self._FLUSH_HUTANG_CUTI,
							qty=sisa_big)
				else:
					"""berarti diberikan cuti tahunan"""
					alokasi = company.hr_holidays_yearly_item.jumlah

					"""alokasi juga dikurangi sisa tahunan jika cuti tahunan punya hutang"""
					is_punya_hutang = False
					if sisa_yearly < 0:
						is_punya_hutang = True
					else:
						if sisa_yearly > max_sisa_yearly:
							alokasi += max_sisa_yearly
						else:
							alokasi += sisa_yearly
					
					if sisa_yearly > 0:
						notes = self._ADD_PREVIOUS_SISA.format({sisa_yearly})

					date_exp = '{0}-{1}-{2}'.format((last_datetime_obj.year + company.hr_holidays_yearly_periodic),
						last_datetime_obj.month, last_datetime_obj.day)

					"""tambahkan alokasi cuti baru"""
					allocation_vals = {
						'name': self._ALLOCATION_YEARLY_NAME,
						'holiday_status_id': company.hr_holidays_yearly_item.id,
						'type': 'add',
						'is_active': True,
						'number_of_days_temp': alokasi,
						'employee_id': employee.id,
						'state': 'confirm',
						'holiday_status_help': 'cuti',
						'date_start': today.strftime(DATE_FORMAT),
						'date_exp': date_exp,
						'notes': notes,
					}

					new_allocation = self.create(allocation_vals)
					new_allocation.sudo().action_validate()

					template = self.env.ref('ka_hr_holidays.template_mail_cuti_allocation')
					self.env['mail.template'].browse(template.id).send_mail(new_allocation.id)

					if is_punya_hutang:
						self.flush_holidays(flush_reference=new_allocation, flush_name=self._FLUSH_HUTANG_CUTI,
							qty=sisa_yearly)

	@api.model
	def check_employee_holidays_allocation(self):
		self._check_holidays_allocation()
		# self._check_holidays_group_approved()
		self._check_holidays_dinas()
		self._check_inhaldagen_active()

	# def _check_holidays_group_approved(self):
	# 	print '------------- check holidays group approved --------------------'
	# 	datetime_obj = self._get_jakarta_timezone(datetime.now())
	# 	str_date = datetime_obj.date().strftime(DATE_FORMAT)
	# 	companies = self.env['res.company'].search([])

	# 	for company in companies:
	# 		if not company.check_requirement():
	# 			continue

	# 		holiday_group = self.env['ka_hr.holidays.group'].search([
	# 			('tgl_holiday', '=', str_date),
	# 			('company_id', '=', company.id),
	# 			('state', '=', 'approved'),
	# 		])

	# 		for group in holiday_group:
	# 			employees = self.env['hr.employee'].search([
	# 				('pensiun', '=', False),
	# 				('company_id', 'child_of', company.id)
	# 			])

	# 			for employee in employees:
	# 				"""cek apakah harinya overlap dengan cuti employee,
	# 				jika overlap, maka tidak perlu dipotong lagi untuk cuti bersama"""
	# 				status_overlap = self.env['hr.holidays.lines'].is_overlap_holiday(employee, group.tgl_holiday)

	# 				if status_overlap:
	# 					continue

	# 				vals = {
	# 					'name': group.name,
	# 					'holiday_address': "Cuti bersama {}".format(group.name),
	# 					'employee_id': employee.id,
	# 					'type': 'remove',
	# 					'holiday_status_id': company.hr_holidays_group_item.id,
	# 					'date_from': group.tgl_holiday,
	# 					'date_to': group.tgl_holiday,
	# 					'number_of_days_temp': 1,
	# 					'holiday_group_id': group.id,
	# 					'state': 'confirm',
	# 					'holiday_status_help': 'cuti',
	# 				}

	# 				new_holiday = self.create(vals)
	# 				new_holiday.sudo().action_validate(is_cuti_bersama=True)
				
	# 			group.action_passed()

	# static
	def bayar_hutang_cuti(self, line_hutang, kompensasi):
		jumlah_hutang = len(line_hutang)
		jumlah_kompensasi = kompensasi.number_of_days_temp
		idx = 0
		hutang_terbayar = []

		for hutang in line_hutang:
			if idx > jumlah_kompensasi:
				break

			hutang.kompensasi_reference_id = kompensasi
			hutang_terbayar.append(hutang)
			idx += 1

		self.flush_holidays(flush_reference=kompensasi, flush_name=self._FLUSH_HUTANG_CUTI,
			qty=idx, line_hutang=line_hutang)

	# static
	def check_employee_has_hutang(self, employee):
		hutang = self.env['hr.holidays.lines'].search([
			('employee_id', '=', employee.id),
			('is_hutang', '=', True),
			('kompensasi_reference_id', '=', False)
		], order='id asc')
		return hutang

	# static
	def _check_holidays_dinas(self):
		"""untuk mengecek dinas, jika pas hari libur maka mendapat inhaldagen"""
		datetime_obj = self._get_jakarta_timezone(datetime.now())
		# datetime_obj = datetime.strptime('2017-12-30', DATE_FORMAT)
		str_date = datetime_obj.date().strftime(DATE_FORMAT)
		companies = self.env['res.company'].search([])

		for company in companies:
			if not company.check_requirement():
				continue

			if not company.today_is_off_day():
				continue

			holiday_dinas_line = self.env['hr.holidays.lines'].search([
				('holiday_date', '=', str_date),
				('company_id', '=', company.id),
				('is_inhaldagen', '=', False),
				('leave_type', '=', 'dinas'),
			])

			for line in holiday_dinas_line:
				holiday_dinas = line.holiday_id
				inhaldagen = self.create_inhaldagen(datetime_obj, holiday_dinas)
				line.is_inhaldagen = True
				line.inhaldagen_reference_id = inhaldagen
				hutang = self.check_employee_has_hutang(line.employee_id)
				if len(hutang) > 0:
					self.bayar_hutang_cuti(hutang, inhaldagen)
					if len(hutang) >= inhaldagen.number_of_days_temp:
						inhaldagen.is_active = False

	def create_inhaldagen(self, date_obj, dinas):
		employee = dinas.employee_id
		alokasi = employee.company_id.hr_holidays_inhaldagen_item.jumlah
		start = date_obj + timedelta(days=1)
		exp = date_obj + timedelta(days=(employee.company_id.hr_holidays_inhaldagen_expire + 1))
		inhaldagen = self.create({
			'name': self._INHALDAGEN_NAME,
			'employee_id': employee.id,
			'type': 'add',
			'number_of_days_temp': alokasi,
			'holiday_status_id': employee.company_id.hr_holidays_inhaldagen_item.id,
			'company_id': employee.company_id.id,
			'notes': self._INHALDAGEN_NOTES.format(dinas.nomor_dinas),
			'holiday_status_help': 'cuti',
			'state': 'confirm',
			'is_active': True,
			'date_exp': exp,
			'date_start': start,
			'is_inhaldagen': True,
			'dinas_reference_id': dinas.id,
		})
		inhaldagen.sudo().action_validate()
		return inhaldagen

	def _check_inhaldagen_active(self):
		"""flush active inhaldagen when not used""" 
		datetime_obj = self._get_jakarta_timezone(datetime.now())
		# datetime_obj = datetime.strptime('2018-01-11', DATE_FORMAT)
		str_date = datetime_obj.date().strftime(DATE_FORMAT)
		companies = self.env['res.company'].search([])

		for company in companies:
			if not company.check_requirement():
				continue

			inhaldagens = self.search([
				('holiday_status_id', '=', company.hr_holidays_inhaldagen_item.id),
				('is_active', '=', True),
				('date_exp', '<=', str_date),
				('company_id', '=', company.id),
			])

			for inhaldagen in inhaldagens:
				self.flush_holidays(flush_reference=inhaldagen, flush_name=self._FLUSH_INHALDAGEN_NAME,
					qty=inhaldagen.number_of_days_temp)
				inhaldagen.is_active = False

class KaHrEmployeeHolidaysLines(models.Model):
	_name = 'hr.holidays.lines'
	_description = "SDM Detail Absensi Pegawai"

	holiday_id = fields.Many2one('hr.holidays', string="Induk Cuti", required=True, ondelete='cascade')
	holiday_date = fields.Date(string="Tanggal Absen", required=True)
	company_id = fields.Many2one(string="Unit/PG", related='holiday_id.company_id')
	leave_type = fields.Selection(related='holiday_id.holiday_status_help')
	employee_id = fields.Many2one(related='holiday_id.employee_id', string="Pegawai")
	cuti_reference_id = fields.Many2one('hr.holidays', string="Referensi Cuti",
		help="Untuk referensi pemotongan cuti yang diambil, khusus untuk type = 'cuti'")
	is_hutang = fields.Boolean(string="Hutang Cuti",
		help="Apakah hutang cuti, khusus untuk type = 'cuti'")
	kompensasi_reference_id = fields.Many2one('hr.holidays', string="Referensi Kompensasi Hutang",
		help="Jika is_hutang = True maka harus ada kompensasi nantinya.")
	is_inhaldagen = fields.Boolean(string="Inhaldagen",
		help="Apakah mendapat inhaldagen, khusus untuk type = 'dinas'")
	inhaldagen_reference_id = fields.Many2one('hr.holidays', string="Referensi Inhaldagen",
		help="Untuk referensi inhaldagen jika is_inhaldagen = True, khusus untuk type = 'dinas'")


	def is_overlap_holiday(self, employee, holiday_date):
		"""helper untuk pengecekan apakah ada holiday yg overlap untuk keperluan cuti bersama"""
		overlap_count = self.search_count([
			('holiday_id.employee_id', '=', employee.id),
			('holiday_date', '=', holiday_date)
		])

		if overlap_count > 0:
			return True
		else:
			return False

	def action_view_all_cuti(self):
		pass

class KaHrHolidaysKompensasiHutangLines(models.Model):
	_name = 'hr.holidays.kompensasi.hutang.lines'
	_description = "SDM Detail Hutang Cuti Pegawai"

	kompensasi_reference_id = fields.Many2one('hr.holidays', string="Referensi Kompensasi",
		required=True, ondelete='cascade')
	hutang_reference_id = fields.Many2one('hr.holidays', string="Referensi Hutang",
		required=True, ondelete='cascade')