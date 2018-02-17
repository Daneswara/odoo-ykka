# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields

class KaHrPangkat(models.Model):
    """Master data of employee job rank.

    _name = 'hr.pangkat'
    """

    _name = 'hr.pangkat'
    _description = "SDM master data kepangkatan karyawan"

    code = fields.Char(string="Kode", size=6, required=True)
    name = fields.Char(string="Nama", size=64, required=True)
    company_id = fields.Many2one('res.company', string="Unit/PG", required=True,
        default=lambda self: self.env.user.company_id)
    employee_ids = fields.One2many('hr.employee', 'pangkat_id', string="Karyawan")

    _sql_constraints = [
		('hr_pangkat_unique', 'UNIQUE(code, company_id)', "Kode sudah digunakan! Silahkan menggunakan kode lainnya.")
	]
