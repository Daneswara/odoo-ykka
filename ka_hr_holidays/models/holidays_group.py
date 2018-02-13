# ----------------------------------------------------------
# Data Cuti Bersama
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from datetime import datetime, date
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

class KaHrHolidaysGroup(models.Model):
	_name = 'ka_hr.holidays.group'
	_description = "SDM Cuti Bersama"

	name = fields.Char(string="Nama", required=True, readonly=True,
		states={'draft': [('readonly', False)]})
	tgl_holiday = fields.Date(string="Tanggal Libur", required=True, default=fields.Date.today,
		readonly=True, states={'draft': [('readonly', False)]})
	company_id = fields.Many2one('res.company', string="Unit/PG", required=True,
		default=lambda self: self.env.user.company_id, readonly=True,
		states={'draft': [('readonly', False)]})
	state = fields.Selection([
		('draft', "Draft"),
		('approved', "Disetujui"),
		# ('passed', "Sudah Dilaksanakan"),
		('canceled', "Batal")
	], string="Status", default='draft')

	_sql_constraints = [
		('holidays_group_unique', 'UNIQUE(company_id, tgl_holiday)', "Data hari cuti bersama tidak boleh ada yg sama!")
	]

	def _check_date_already_passed(self):
		"""untuk mengecek apakah hari sudah terlewati dari hari ini"""
		today = date.today()
		date_obj = datetime.strptime(self.tgl_holiday, DATE_FORMAT).date()
		return today >= date_obj

	# Override
	@api.multi
	def unlink(self):
		for s in self:
			if s.state == 'approved':
				raise ValidationError("Data yang sudah disetujui, tidak dapat dihapus!")

			if s.state == 'passed':
				raise ValidationError("Data yang sudah terlewati, tidak dapat dihapus!")

		return super(KaHrHolidaysGroup, self).unlink()

	@api.constrains('tgl_holiday', 'company_id')
	def _onchange_check_off_day(self):
		for s in self:
			if self._check_date_already_passed():
				raise ValidationError("Tanggal cuti sudah terlewati!")

			off_day = s.company_id.get_off_day()
			date_obj = datetime.strptime(s.tgl_holiday, DATE_FORMAT).date()
			idx = date_obj.weekday()
			if idx in off_day:
				raise ValidationError("Tanggal cuti adalah tanggal hari libur perusahaan!")

	# @api.multi
	# def action_approve(self):
	# 	if self._check_date_already_passed():
	# 		raise ValidationError("Data yang sudah terlewati, tidak dapat disetujui!")
		
	# 	if not self.company_id.check_requirement():
	# 		raise ValidationError(self.company_id.NO_CONFIG_MESSAGE)

	# 	self.state = 'approved'

	@api.multi
	def action_approve(self):
		if self._check_date_already_passed():
			raise ValidationError("Data yang sudah terlewati, tidak dapat disetujui!")

		company = self.company_id
		if not company.check_requirement():
			raise ValidationError(company.NO_CONFIG_MESSAGE)

		employees = self.env['hr.employee'].search([
			('pensiun', '=', False),
			('company_id', 'child_of', self.company_id.id)
		])

		for employee in employees:
			"""cek apakah harinya overlap dengan cuti employee,
			jika overlap, maka tidak perlu dipotong lagi untuk cuti bersama"""
			status_overlap = self.env['hr.holidays.lines'].is_overlap_holiday(employee, self.tgl_holiday)

			if status_overlap:
				continue

			vals = {
				'name': self.name,
				'holiday_address': "Cuti bersama {}".format(self.name),
				'employee_id': employee.id,
				'type': 'remove',
				'holiday_status_id': company.hr_holidays_group_item.id,
				'date_from': self.tgl_holiday,
				'date_to': self.tgl_holiday,
				'number_of_days_temp': 1,
				'holiday_group_id': self.id,
				'state': 'confirm',
				'holiday_status_help': 'cuti',
			}

			new_holiday = self.env['hr.holidays'].create(vals)
			new_holiday.sudo().action_validate(is_cuti_bersama=True)
		
		self.state = 'approved'

	def delete_link(self):
		holidays = self.env['hr.holidays'].search([('holiday_group_id', '=', self.id)])
		for holiday in holidays:
			holiday.sudo().state = 'draft'
			holiday.sudo().unlink()

	@api.multi
	def action_draft(self):
		if self._check_date_already_passed():
			raise ValidationError("Data yang sudah terlewati, tidak dapat diubah!")

		# if self.state == 'passed':
		# 	raise ValidationError("Cuti bersama yang sudah dijalani, tidak dapat dihapus!")

		self.delete_link()
		self.state = 'draft'

	@api.multi
	def action_cancel(self):
		if self._check_date_already_passed():
			raise ValidationError("Data yang sudah terlewati, tidak dapat dihapus!")

		# if self.state == 'passed':
		# 	raise ValidationError("Cuti bersama yang sudah dijalani, tidak dapat dihapus!")

		self.delete_link()
		self.state = 'canceled'

	# @api.multi
	# def action_passed(self):
	# 	self.state = 'passed'