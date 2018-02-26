# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api

class KaHrPayrollScaleType(models.Model):
    _name = 'ka_hr_payroll.scale.type'

    code = fields.Char(string="Kode", size=3, required=True)
    name = fields.Char(string="Nama", size=64, required=True)

class KaHrPayrollScale(models.Model):
    _name = 'ka_hr_payroll.scale'
    _description = "Data skala karyawan"
    _order = 'date_start desc'

    date_start = fields.Date(string="Tanggal Mulai", required=True, readonly=True,
        default=fields.Date.today, states={'draft': [('readonly', False)]})
    min_scale = fields.Float(string="Skala Awal", digits=(6,3), required=True, readonly=True,
        default=1.000, states={'draft': [('readonly', False)]})
    max_scale = fields.Float(string="Skala Akhir", digits=(6,3), required=True, readonly=True,
        default=1.000, states={'draft': [('readonly', False)]})
    value_start = fields.Float(string="Nilai Awal", required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    delta = fields.Float(string="Nilai Delta", required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    golongan_id = fields.Many2one('hr.golongan', string="Golongan", required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    type_id = fields.Many2one('ka_hr_payroll.scale.type', string="Tipe", required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', "Draft"),
        ('approved', "Disetujui"),
        ('canceled', "Dibatalkan"),
    ], string="Status", default='draft')
    line_ids = fields.One2many('ka_hr_payroll.gapok.scale.lines', 'gapok_scale_id', readonly=True,
        states={'draft': [('readonly', False)]})
