# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from datetime import datetime

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

class KaHrEmployee(models.Model):
	"""Master data of employee.

	_inherit = 'hr.employee'
	"""

	_inherit = 'hr.employee'

	nik = fields.Char(string='N I K', size=10, required=True)
	position = fields.Char(string="Posisi", compute="_complite_position")
	address = fields.Char(string='Alamat', size=64)
	city = fields.Char(string='Kota', size=32)
	tgl_masuk = fields.Date(string='Tgl. Masuk', required=True)
	home_phone = fields.Char(string='Telepon Rumah', size=16)
	category_id = fields.Many2one('hr.category', string='Kategori')
	npwp = fields.Char(string='NPWP', size=32)
	bank_id = fields.Many2one('res.bank', string='Bank')
	acc_number = fields.Char(string='No. Rekening', size=32)
	acc_name = fields.Char(string='Atas Nama', size=32)
	place_birthday = fields.Char(string='Kelahiran', size=32)
	graduate_ids = fields.One2many('hr.employee.graduate', 'employee_id', string='Pendidikan Formal')
	course_ids = fields.One2many('hr.employee.course', 'employee_id', string=' Pendidikan Non Formal')
	pensiun = fields.Boolean('Pensiun')
	religion = fields.Selection([
		('islam','Islam'),
		('kristen','Kristen'),
		('katolik','Katolik'),
		('hindu','Hindu'),
		('budha','Budha'),
		('lain','Lain-nya'),
	], 'Agama')

	# gaji_pokok = fields.Float(string="Gaji Pokok", required=True)
	hub_kerja_id = fields.Many2one('ka_hr.hubungan.kerja', string="Hub. Kerja")
	is_tetap = fields.Boolean(string="Pegawai Tetap")
	tgl_tetap = fields.Date(string="Tanggal Pengangkatan", help="Tanggal pengangkatan sebagai pegawai tetap.")
	tgl_pensiun = fields.Date(compute='_compute_birthday', string="Tanggal Pensiun", store=True,
		help="Tanggal pensiun pegawai.")
	tgl_mpp = fields.Date(compute='_compute_birthday', string="Tanggal MPP", store=True,
		help="Tanggal persiapan pensiun pegawai.")

	pangkat_id = fields.Many2one('hr.pangkat', string="Pangkat")
	golongan_id = fields.Many2one('hr.golongan', string="Golongan")

	employee_keluarga_ids = fields.One2many('ka_hr.employee.keluarga', 'employee_id')
	employee_history_ids = fields.One2many('hr.employee.history', 'employee_id')

	# Override
	@api.onchange('user_id')
	def _onchange_user(self):
		pass

	@api.model
	def create(self, vals):
		"""Override method `create()`. Use for insert data

		Decorators:
			api.model

		Arguments:
			vals {Dict} -- Values insert data

		Returns:
			Recordset -- Create result will return recordset
		"""
		employee = super(KaHrEmployee, self).create(vals)
		employee.create_employee_history()
		return employee

	@api.multi
	def write(self, vals):
		"""Override method `write()`. Use for update data

		Decorators:
			api.multi

		Arguments:
			vals {dict} -- Values update data

		Returns:
			Boolean -- Update result will return boolean
		"""
		is_change_history = False

		if 'department_id' in vals or 'job_id' in vals or 'pangkat_id' in vals or \
			'golongan_id' in vals or 'company_id' in vals:
				is_change_history = True

		employee = super(KaHrEmployee, self).write(vals)
		if is_change_history:
			self.create_employee_history()
		return employee

	def create_employee_history(self):
		"""Insert data to `hr.employee.history`
		"""
		self.env['hr.employee.history'].create({
			'employee_id': self.id,
			'department_id': self.department_id.id,
			'job_id': self.job_id.id,
			'pangkat_id': self.pangkat_id.id,
			'golongan_id': self.golongan_id.id,
			'company_id': self.company_id.id,
		})

	# def action_view_presensi(self):
	# 	action = self.env.ref('ka_hr_pegawai.action_ka_hr_presensi')
	# 	result = action.read()[0]
	# 	result['domain'] = [('employee_id', '=', self.id)]
	# 	return result

	# def action_view_lembur(self):
	# 	action = self.env.ref('ka_hr_pegawai.action_ka_hr_lembur')
	# 	result = action.read()[0]
	# 	result['domain'] = [('employee_id', '=', self.id)]
	# 	return result

	@api.multi
	def _complite_position(self):
		for rec in self:
			company = rec.company_id.name or ''
			department = rec.department_id.name or ''
			job = rec.job_id.name or ''
			rec.position = company + '/' + department + '/' + job

	# def action_view_absensi(self):
	# 	action = self.env.ref('ka_hr_pegawai.action_hr_holidays')
	# 	result = action.read()[0]
	# 	result['domain'] = ['&', ('employee_id', '=', self.id), ('type', '=', 'remove')]
	# 	result['context'] = {
	# 		'default_employee_id': self.id,
	# 		'default_type': 'remove'
	# 	}
	# 	return result

	# def action_view_cuti(self):
	# 	action = self.env.ref('ka_hr_pegawai.action_ka_hr_employee_cuti')
	# 	result = action.read()[0]
	# 	result['domain'] = [('employee_id', '=', self.id)]
	# 	result['context'] = {
	# 		'default_employee_id': self.id
	# 	}
	# 	return result

	# def action_ambil_cuti(self):
	# 	return {
	# 		'name': ('Ambil Cuti'),
	# 		'view_type': 'form',
	# 		'view_mode': 'form,tree',
	# 		'res_model': 'hr.holidays',
	# 		'view_id': False,
	# 		'type': 'ir.actions.act_window',
	# 		'target':'current',
	# 		'context': {
	# 			'default_employee_id': self.id,
	# 			'default_company_id':self.company_id.id
	# 		}
	# 	}

	@api.depends('birthday')
	def _compute_birthday(self):
		for s in self:
			if not s.company_id.hr_pensiun_age or not s.company_id.hr_mpp_month:
				continue

			if s.birthday:
				date_now = datetime.now().date()
				birthday_obj = datetime.strptime(s.birthday, DATE_FORMAT).date()
				selisih = date_now - birthday_obj
				selisih_year = selisih.days / 365
				sisa_year = s.company_id.hr_pensiun_age - selisih_year
				pensiun_year = date_now.year + sisa_year
				pensiun_obj = datetime.strptime('{}-{}-{}'.format(pensiun_year, birthday_obj.month, birthday_obj.day), DATE_FORMAT)
				pensiun_new = pensiun_obj
				pensiun_month = pensiun_obj.month
				if pensiun_obj.day > 1:
					if pensiun_obj.month >= 12:
						pensiun_month = 1
						pensiun_year += 1
					else:
						pensiun_month += 1
					pensiun_new = datetime.strptime('{}-{}-{}'.format(pensiun_year, pensiun_month, 1), DATE_FORMAT)

				s.tgl_pensiun = pensiun_new

				mpp_month = pensiun_month
				mpp_year = pensiun_year
				if pensiun_month <= s.company_id.hr_mpp_month:
					mpp_month = (12 + pensiun_month)
					mpp_year -= 1
				mpp_month -= s.company_id.hr_mpp_month

				s.tgl_mpp = datetime.strptime('{}-{}-{}'.format(mpp_year, mpp_month, 1), DATE_FORMAT)
			else:
				s.tgl_pensiun = None

	@api.multi
	def action_view_sp(self):
		action = self.env.ref('ka_hr_pegawai.action_employee_sp')
		result = action.read()[0]
		result['domain'] = [('employee_id', '=', self.id), ('state', '!=', 'draft')]
		result['context'] = {
			'default_employee_id': self.id
		}
		return result