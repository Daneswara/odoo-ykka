# ----------------------------------------------------------
# Untuk pengkategorian karyawan
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields, api

class hr_category(models.Model):
	_name = 'hr.category'
	_description = "SDM Jabatan"

	name = fields.Char('Nama Jabatan', size=32, required=True)
	jml_pegawai = fields.Integer(compute='_compute_no_of_employee', string='Jml. Pegawai')
	employee_ids = fields.One2many('hr.employee', 'category_id', string='Pegawai', groups='base.group_user')
	company_id = fields.Many2one('res.company', string="Unit/PG", required=True, default=lambda self: self.env.user.company_id)

	_sql_constraints = [
		('kategori_company_uniq', 'unique(name, company_id)', 'Dalam satu Unit/PG Nama kategori tidak boleh sama !'),
	]

	@api.depends('employee_ids')
	def _compute_no_of_employee(self):
		self.jml_pegawai = len(self.employee_ids or [])