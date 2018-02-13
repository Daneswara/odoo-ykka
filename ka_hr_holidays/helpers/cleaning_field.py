# ----------------------------------------------------------
# Helpers untuk cleaning field yg tidak digunakan
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# --------------------------------------------------------

from odoo import models, fields, api

class KaHrHolidaysCleanField(models.TransientModel):
	_name = 'ka_hr.holidays.clean.field'

	def _remove_field(self, table_name, column_name):
		sql = """ALTER TABLE %s
			DROP COLUMN IF EXISTS %s""" % (table_name, column_name)

		self._cr.execute(sql)

	def _drop_table(self, table_name):
		sql = """DROP TABLE IF EXISTS %s CASCADE""" % (table_name,)
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
		self._remove_field('res_company', 'hr_holidays_yearly_allocation')
		self._remove_field('res_company', 'hr_holidays_big_allocation')
		self._remove_field('res_company', 'hr_pengurang_cuti_bersama')
		self._remove_field('res_company', 'hr_holidays_public_item')
		self._remove_field('hr_holidays', 'active')
		self._remove_field('hr_holidays', 'holiday_parent')
		self._remove_field('hr_holidays', 'inhaldagen_expire_date')
		self._remove_field('ka_hr_holidays_public', 'keterangan')
		self._remove_field('ka_hr_holidays_public', 'holiday_date')
		self._drop_model('ka_hr.holidays.sale')
		