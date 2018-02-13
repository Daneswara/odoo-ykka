# ----------------------------------------------------------
# Data jual cuti besar
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ---------------------------------------------------------

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class KaHrHolidaysAfkoop(models.Model):
	_name = 'ka_hr.holidays.afkoop'
	_description = "SDM Jual Cuti Besar"

	_SALE_NAME = "Jual jatah cuti besar"

	def _default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	employee_id = fields.Many2one('hr.employee', string="Nama Pegawai", required=True,
		index=True, domain=[('pensiun', '=', False)], default=_default_employee)
	jumlah = fields.Selection([
		('1', "1 Bulan"),
		('2', "2 Bulan"),
	], string="Jumlah", required=True, readonly=True, states={'draft': [('readonly', False)]})
	sisa_cuti = fields.Integer(related='employee_id.count_holidays_big', string="Sisa Cuti Besar")
	state = fields.Selection([
		('draft', "Draft"),
		('proposed', "Pengajuan"),
		('approved', "Disetujui"),
		('refused', "Ditolak"),
		('canceled', "Dibatalkan"),
	], string="Status", required=True, default='draft')
	parent_holiday = fields.Many2one('hr.holidays', compute='_compute_sisa_cuti', string="Parent", store=True)
	company_id = fields.Many2one(related='employee_id.company_id', string="Unit/PG",
		required=True, readonly=True)
	holiday_id = fields.Many2one('hr.holidays', string="Referensi") # sebagai referensi saat approve hr.holidays di-flush

	user_id = fields.Many2one(related='employee_id.user_id', string="User")

	@api.model
	def create(self, vals):
		if not vals.has_key('company_id'):
			employee = self.env['hr.employee'].browse(vals['employee_id'])
			vals['company_id'] = employee.company_id.id

	@api.constrains('employee_id', 'jumlah')
	def _check_big_holidays(self):
		for s in self:
			if s.sisa_cuti > 0:
				if s.jumlah == '1':
					if s.sisa_cuti / 30 < 1:
						"""error jatah kurang dari 30 hari"""
						raise ValidationError("Permintaan tidak dapat diproses! Sisa cuti kurang dari 30 hari!")
				else:
					if s.sisa_cuti / 60 < 1:
						"""error jatah kurang dari 60 hari"""
						raise ValidationError("Permintaan tidak dapat diproses! Sisa cuti kurang dari 60 hari!")
			else:
				"""error karena tidak ada jatah holidays"""
				raise ValidationError("Permintaan tidak dapat diproses! Anda tidak mempunyai jatah cuti besar!")

	# @override
	@api.multi
	def name_get(self):
		res = []
		for s in self:
			name = s.employee_id.name or ''
			res.append((s.id, name))

		return res

	@api.multi
	def action_draft(self):
		self.state = 'draft'

	@api.multi
	def action_propose(self):
		self.state = 'proposed'

	@api.multi
	def action_approve(self):
		if self.sisa_cuti > 0:
			if self.jumlah == '1':
				if self.sisa_cuti / 30 < 1:
					"""error jatah kurang dari 30 hari"""
					raise ValidationError("Permintaan tidak dapat diproses! Sisa cuti kurang dari 30 hari!")
			else:
				if self.sisa_cuti / 60 < 1:
					"""error jatah kurang dari 60 hari"""
					raise ValidationError("Permintaan tidak dapat diproses! Sisa cuti kurang dari 60 hari!")
		else:
			"""error karena tidak ada jatah holidays"""
			raise ValidationError("Permintaan tidak dapat diproses! Anda tidak mempunyai jatah cuti besar!")

		holidays_big = self.company_id.hr_holidays_big_item
		num_of_days = 30 if self.jumlah == '1' else 60
		vals = {
			'name': self._SALE_NAME,
			'holiday_status_id': holidays_big.id,
			'type': 'flush',
			'number_of_days_temp': num_of_days,
			'parent_id': self.parent_holiday.id,
			'employee_id': self.employee_id.id,
			'state': 'confirm',
		}

		flush = self.env['hr.holidays'].create(vals)
		flush.sudo().action_validate()
		
		self.holiday_id = flush
		self.state = 'approved'

	@api.multi
	def action_refuse(self):
		self.state = 'refused'

	@api.multi
	def action_cancel(self):
		self.state = 'canceled'