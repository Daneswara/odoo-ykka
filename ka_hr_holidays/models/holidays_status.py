# ----------------------------------------------------------
# Data Kategori Absensi Pegawai
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields, api

class KaHrHolidaysStatus(models.Model):
	_inherit = 'hr.holidays.status'
	_description = "SDM Kategori Absensi Pegawai"

	"""Override fields"""
	company_id = fields.Many2one('res.company', string="Unit/PG", required=True, default=lambda self: self.env.user.company_id)
	"""End of override fields"""

	code = fields.Char(string="Kode", size=3, required=True)
	leave_type = fields.Selection([
		('cuti', "Cuti"),
		('ijin', "Ijin"),
		('dinas', "Dinas"),
		('sakit', "Sakit"),
		('mangkir', "Mangkir")
	], string="Jenis Absensi", required=True)
	jumlah = fields.Integer(string="Jumlah Alokasi", required=True)
	satuan = fields.Selection([
		('hari', "Hari"),
		('bulan', "Bulan")
	], string="Satuan Absensi", required=True)
	holiday_type = fields.Selection([
		('add', 'Add'),
		('remove', 'Remove'),
	], default='remove', string="Tipe Absensi", required=True, help="Tipe holiday, jika 'Add', maka tampil di hr.holidays 'type' = 'add' dan sebaliknya.")
	is_potong_gaji = fields.Boolean(string="Potong Gaji")
	is_daily_type = fields.Boolean(string="Absensi Harian",
		help="Penentuan tipe pengambilan cuti.\nJika 'True' maka cuti diambil harian dan tidak dipotong saat libur.")
	# is_need_parent = fields.Boolean(string="Dengan Referensi",
	# 	help="Penentuan referensi pengambilan cuti.\nJika 'True' maka cuti harus punya referensi cuti yang diambil.")

	_sql_constraints = [
		('holidays_status_unique', 'UNIQUE(company_id, code)', "Data kategori absensi tidak boleh ada yang sama!")
	]

	# @override
	@api.multi
	def name_get(self):
		res = []
		for s in self:
			code = s.code or ''
			name = s.name or ''
			res.append((s.id, code + ' - ' + name))

		return res

	# @override
	@api.model
	def name_search(self, name='', args=None, operator='ilike', limit=80):
		if not args:
			args = []

		if name:
			record = self.search(['|', ('name', operator, name), ('code', operator, name)] + args, limit=limit)
		else:
			record = self.search(args, limit=limit)

		return record.name_get()

	# Override
	@api.multi
	def get_days(self, employee_id):
		# need to use `dict` constructor to create a dict per id
		result = dict((id, dict(max_leaves=0, leaves_taken=0, remaining_leaves=0, virtual_remaining_leaves=0)) for id in self.ids)

		# parameter tambahan, agar mencari yg active saja
		holidays = self.env['hr.holidays'].search([
			('employee_id', '=', employee_id),
			('state', 'in', ['confirm', 'validate1', 'validate']),
			('holiday_status_id', 'in', self.ids),
			('is_active', '=', True),
		])

		for holiday in holidays:
			status_dict = result[holiday.holiday_status_id.id]
			if holiday.type == 'add':
				if holiday.state == 'validate':
					# note: add only validated allocation even for the virtual
					# count; otherwise pending then refused allocation allow
					# the employee to create more leaves than possible
					status_dict['virtual_remaining_leaves'] += holiday.number_of_days_temp
					status_dict['max_leaves'] += holiday.number_of_days_temp
					status_dict['remaining_leaves'] += holiday.number_of_days_temp
			elif holiday.type == 'remove' or holiday.type == 'flush':  # number of days is negative
				status_dict['virtual_remaining_leaves'] -= holiday.number_of_days_temp
				if holiday.state == 'validate':
					status_dict['leaves_taken'] += holiday.number_of_days_temp
					status_dict['remaining_leaves'] -= holiday.number_of_days_temp
		return result