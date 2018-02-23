# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields

class KaHrGolongan(models.Model):
    """Master data of employee job group (golongan).

    _name = 'hr.golongan'
    """

    _name = 'hr.golongan'
    _description = "SDM master data golongan karyawan"

    name = fields.Char(string="Nama", size=12, required=True)
    company_id = fields.Many2one('res.company', string="Unit/PG", required=True,
        default=lambda self: self.env.user.company_id)
    employee_ids = fields.One2many('hr.employee', 'golongan_id', string="Karyawan")
