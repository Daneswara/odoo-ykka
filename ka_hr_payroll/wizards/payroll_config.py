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

    company_id = fields.Many2one('res.company', string="Unit/PG", required=True,
        default=lambda self: self.env.user.company_id)
    konjungtur_gaji = fields.Float(related='company_id.konjungtur_gaji', string="Konjungtur Gaji", required=True)
    konjungtur_pensiun = fields.Float(related='company_id.konjungtur_pensiun', string="Konjungtur Pensiun", required=True)

    @api.multi
    def save_data(self):
        """To save data wizard. Called from button.

        Decorators:
            api.multi
        """
        self.company_id.konjungtur_gaji = self.konjungtur_gaji
        self.company_id.konjungtur_pensiun = self.konjungtur_pensiun
