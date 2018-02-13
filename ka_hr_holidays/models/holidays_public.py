# ----------------------------------------------------------
# Data hari libur / hari raya nasional
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

class KaHrHolidaysPublic(models.Model):
	_name = 'ka_hr.holidays.public'
	_description = "SDM Hari Libur / Hari Raya Nasional"

	name = fields.Char(string="Nama", required=True)
	tgl_holiday = fields.Date(string="Tanggal Libur", required=True, default=fields.Date.today)
	company_id = fields.Many2one('res.company', string="Unit/PG", required=True, default=lambda self: self.env.user.company_id)

	_sql_constraints = [
		('holidays_public_unique', 'UNIQUE(tgl_holiday, company_id)', "Data hari libur nasional / hari raya tidak boleh ada yg sama!")
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
			if s._check_date_already_passed():
				raise ValidationError("Data yang sudah terlewati, tidak dapat dihapus!")

		return super(KaHrHolidaysPublic, self).unlink()