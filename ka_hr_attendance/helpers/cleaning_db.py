# ----------------------------------------------------------
# Helpers untuk cleaning db yg tidak digunakan
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# --------------------------------------------------------

from odoo import models, fields, api

class KaHrAttendanceCleanDB(models.TransientModel):
	_name = 'ka_hr_attendance.clean.db'

	def _drop_column(self, table_name, column_name):
		sql = """ALTER TABLE %s
			DROP COLUMN IF EXISTS %s""" % (table_name, column_name)

		self._cr.execute(sql)

	def _drop_table(self, table_name):
		sql = """DROP TABLE IF EXISTS %s CASCADE""" % (table_name,)
		self._cr.execute(sql)

	def _drop_constraint(self, table_name, constraint_name):
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
	def do_clean_db(self):
		"""cleaning database."""
		self._drop_model('ka_hr_attendance.weekly.report.wizard')
		self._drop_model('hr.attendance.shift.lines')
		self._drop_column('hr_attendance_shift', 'tolerance')