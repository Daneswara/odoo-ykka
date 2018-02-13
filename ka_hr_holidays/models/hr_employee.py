# ----------------------------------------------------------
# Data Pegawai
# inherit hr.employee
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ---------------------------------------------------------

from odoo import models, fields, api

class KaHrHolidaysEmployee(models.Model):
	_inherit = 'hr.employee'

	count_holidays_yearly = fields.Integer(compute='_compute_holidays_yearly', string="Cuti Tahunan")
	count_holidays_big = fields.Integer(compute='_compute_holidays_big', string="Cuti Besar")
	count_holidays_inhaldagen = fields.Integer(compute='_compute_holidays_inhaldagen', string="Inhaldagen")

	@api.multi
	def _compute_holidays_yearly(self):
		for employee in self:
			company = employee.company_id
			if not company.check_requirement():
				continue

			holidays_yearly = company.hr_holidays_yearly_item
			holidays = self.env['hr.holidays'].get_sisa_holidays(employee, holidays_yearly)
			employee.count_holidays_yearly = holidays['sisa']

	@api.multi
	def _compute_holidays_big(self):
		for employee in self:
			company = employee.company_id
			if not company.check_requirement():
				continue

			holidays_big = company.hr_holidays_big_item
			holidays = self.env['hr.holidays'].get_sisa_holidays(employee, holidays_big)
			employee.count_holidays_big = holidays['sisa']

	@api.multi
	def _compute_holidays_inhaldagen(self):
		for employee in self:
			company = employee.company_id
			if not company.check_requirement():
				continue

			employee.count_holidays_inhaldagen = self.env['hr.holidays'].get_sisa_inhaldagen(employee)

	def action_view_cuti_tahunan(self):
		yearly_leaves = self.company_id.hr_holidays_yearly_item
		action = self.env.ref('ka_hr_holidays.action_view_allocation')
		result = action.read()[0]
		result['domain'] = [
			('employee_id', '=', self.id),
			('type', '=', 'add'),
			('holiday_status_id', '=', yearly_leaves.id),
		]
		result['context'] = {
			'search_default_allocations_now': 1,
		}
		return result

	def action_view_cuti_besar(self):
		big_leaves = self.company_id.hr_holidays_big_item
		action = self.env.ref('ka_hr_holidays.action_view_cuti')
		result = action.read()[0]
		result['domain'] = [
			('employee_id', '=', self.id),
			('type', '=', 'add'),
			('holiday_status_id', '=', big_leaves.id),
		]
		result['context'] = {
			'search_default_allocations_now': 1,
		}
		return result

	def action_view_inhaldagen(self):
		pass