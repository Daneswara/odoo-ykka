# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api

class KaHrPayrollConfigWizard(models.TransientModel):
    """Wizard to configure models which related with this module
    """

    _name = 'ka_hr_payroll.config.wizard'

    def default_config(self):
		"""To get default config from `ka_hr_payroll.config` model.
		Query `ka_hr_payroll.config` for first record only.
		"""
		config = self.env['ka_hr_payroll.config'].search([], order='id asc', limit=1)
		if not config:
			config = self.env['ka_hr_payroll.config'].create({'konjungtur_gaji': 100, 'konjungtur_dapen': 100})
			self._cr.commit()
		return config

    config_id = fields.Many2one('ka_hr_payroll.config', string="Config", default=default_config)
    konjungtur_gaji = fields.Float(related='config_id.konjungtur_gaji', string="Konjungtur Gaji", required=True,
        default=100, help="Nilai prosentase index konjungtur gaji karyawan.")
    konjungtur_dapen = fields.Float(related='config_id.konjungtur_dapen', string="Konjungtur Dapen", required=True,
        default=100, help="Nilai prosentase index konjungtur pensiun Dapen.")

    @api.multi
    def save_data(self):
        """To save data wizard. Called from button.

        Decorators:
            api.multi
        """
        self.config_id.konjungtur_gaji = self.konjungtur_gaji
        self.config_id.konjungtur_dapen = self.konjungtur_dapen
