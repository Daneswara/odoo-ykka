# -*- coding: utf-8 -*-

"""Data `res_company` yang terkait dengan payroll

Author:
    @CakJuice <hd.brandoz@gmail.com>
"""

from odoo import models, fields, api

class KaPayrollResCompany(models.Model):
    """Inherit dari `res.company`
    """

    _inherit = 'res.company'

    konjungtur = fields.Float("Konjungtur", required=True, default=1.0)