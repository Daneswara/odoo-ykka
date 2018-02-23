# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields

class KaHrEmployeeHistory(models.Model):
    """Data of employee job history.

    _name = 'hr.employee.history'
    """

    _name = 'hr.employee.history'
    _order = 'date_start asc'
    _description = "SDM histori data kepegawaian karyawan"

    date_start = fields.Date(string="Tanggal Mulai", required=True, default=fields.Date.today)
    employee_id = fields.Many2one('hr.employee', string="Karyawan", required=True)
    department_id = fields.Many2one('hr.department', string="Departemen")
    job_id = fields.Many2one('hr.job', string="Jabatan")
    pangkat_id = fields.Many2one('hr.pangkat', string="Pangkat")
    golongan_id = fields.Many2one('hr.golongan', string="Golongan")
    company_id = fields.Many2one('res.company', string="Unit/PG")
    notes = fields.Char(string="Keterangan", size=255)
