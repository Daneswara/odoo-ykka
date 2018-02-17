# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields

class KaHrPayrollResCompany(models.Model):
    """Master data of company (Unit/PG).

    _inherit = 'res.company'
    """

    _inherit = 'res.company'

    konjungtur_gaji = fields.Float("Konjungtur Gaji", required=True, default=100.0)
    konjungtur_pensiun = fields.Float("Konjungtur Pensiun", required=True, default=100.0)
