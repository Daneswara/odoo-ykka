# ----------------------------------------------------------
# Helpers untuk cleaning field yg tidak digunakan
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# --------------------------------------------------------

from odoo import models, fields, api

class KaHrHolidaysCleanField(models.TransientModel):
	_name = 'ka_hr.pegawai.clean.field'

	def _remove_field(self, table_name, column_name):
		sql = """ALTER TABLE %s
			DROP COLUMN IF EXISTS %s""" % (table_name, column_name)

		self._cr.execute(sql)

	def _drop_table(self, table_name):
		sql = """DROP TABLE IF EXISTS %s CASCADE""" % (table_name,)
		self._cr.execute(sql)

	def _drop_table_constraint(self, table_name, constraint_name):
		sql = """ALTER TABLE IF EXISTS %s
			DROP CONSTRAINT IF EXISTS %s""" % (table_name, constraint_name)
		self._cr.execute(sql)

	def _drop_model(self, model_name):
		table_name = model_name.replace('.', '_')
		self._drop_table(table_name)

		sql_model = """SELECT id FROM ir_model WHERE model = '%s'""" % (model_name,)
		self._cr.execute(sql_model)
		fetch = self._cr.fetchone()

		if fetch and len(fetch) > 0:
			sql_model_constraint = """DELETE FROM ir_model_constraint WHERE model = %d""" % (fetch[0],)
			self._cr.execute(sql_model_constraint)
			sql_delete = """DELETE FROM ir_model WHERE id = '%d'""" % (fetch[0],)
			self._cr.execute(sql_delete)

	@api.model
	def do_clean_field(self):
		"""Removes the Field from the database."""
		self._drop_table_constraint('ka_hr_payroll_tunjangan_lines', 'payroll_tunjangan_unique')
		self._drop_model('ka_hr.payroll.tunjangan.lines')
		self._drop_table_constraint('ka_hr_employee_tunjangan_lines', 'employee_tunjangan_unique')
		self._drop_model('ka_hr.employee.tunjangan.lines')
		self._drop_table_constraint('ka_hr_employee_potongan_lines', 'employee_potongan_unique')
		self._drop_model('ka_hr.employee.potongan.lines')
		self._drop_table_constraint('ka_hr_payroll_potongan_lines', 'payroll_potongan_unique')
		self._drop_model('ka_hr.payroll.potongan.lines')
		self._drop_model('ka_hr.tunjangan')
		self._drop_model('ka_hr.potongan')
		self._drop_table_constraint('ka_hr_payroll', 'payroll_unique')
		self._drop_model('ka_hr.payroll')
		self._drop_table_constraint('ka_hr_activity', 'activity_unique')
		self._drop_model('ka_hr.activity')
		self._drop_table_constraint('ka_hr_presensi', 'presensi_unique')
		self._drop_model('ka_hr.presensi')
		self._drop_table_constraint('ka_hr_absensi', 'absensi_unique')
		self._drop_model('ka_hr.absensi')
		self._drop_table_constraint('lembur_unique', 'absensi_unique')
		self._drop_model('ka_hr.lembur')
		self._drop_table_constraint('ka_hr_employee_cuti', 'employee_cuti_unique')
		self._drop_model('ka_hr.employee.cuti')
		self._drop_model('ka_hr.absensi.category')
		self._drop_model('ka_hr.payroll.category')
		self._drop_model('ka_hr.employee.hubungan.keluarga.lines')
		self._drop_model('ka_hr.tunjangan.lines')
		self._drop_model('ka_hr.potongan.lines')
		self._drop_model('ka_hr.payroll.jenis')
		self._drop_model('ka_hr.activity.presensi.wizard')
		self._drop_model('ka_hr.holiday')
		self._drop_model('ka_hr.cuti')
		self._drop_model('ka_hr.absensi')
		self._drop_model('ka_hr.absensi.jenis')
		self._drop_model('report.ka_hr_pegawai.report_ka_hr_activity_presensi_weekly_view')
		self._drop_table_constraint('hr_category', 'kategori_company_uniq')
		self._drop_model('hr.category')
		self._remove_field('hr_employee', 'category_id')
		self._drop_model('ka_hr.hubungan.kerja')
		self._remove_field('hr_employee', 'hub_kerja_id')
