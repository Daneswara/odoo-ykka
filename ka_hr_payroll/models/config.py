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

    DEFAULT_KONJUNGTUR_GAJI = 100
    DEFAULT_KONJUNGTUR_DAPEN = 100

    konjungtur_gaji = fields.Float(string="Konjungtur Gaji (%)", required=True, default=DEFAULT_KONJUNGTUR_GAJI,
        help="Nilai prosentase index konjungtur gaji karyawan.")
    konjungtur_dapen = fields.Float(string="Konjungtur Dapen (%)", required=True, default=DEFAULT_KONJUNGTUR_DAPEN,
        help="Nilai prosentase index konjungtur pensiun Dapen.")

    def default_config(self):
        """To get default config. Querying for first record only.

        Returns:
            Recordset -- Result default config
        """
        config = self.search([], limit=1, order='id asc')
        if not config:
            config = self.create({
                'konjungtur_gaji': self.DEFAULT_KONJUNGTUR_GAJI,
                'konjungtur_dapen': self.DEFAULT_KONJUNGTUR_DAPEN,
            })
            self._cr.commit()
        return config
