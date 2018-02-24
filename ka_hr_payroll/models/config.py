# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields

class KaHrPayrollConfig(models.Model):
    """Setting for `ka_hr_payroll` modules, which call in `ka_hr_payroll.config.wizard`.
	This model just only have 1 record for config, so the `ka_hr_payroll.config.wizard` only call first record.

	_name = 'hr.config'
	"""

    _name = 'ka_hr_payroll.config'

    konjungtur_gaji = fields.Float(string="Konjungtur Gaji (%)", required=True, default=100,
        help="Nilai prosentase index konjungtur gaji karyawan.")
    konjungtur_dapen = fields.Float(string="Konjungtur Dapen (%)", required=True, default=100,
        help="Nilai prosentase index konjungtur pensiun Dapen.")
