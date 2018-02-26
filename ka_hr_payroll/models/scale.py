# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api

class KaHrPayrollScaleType(models.Model):
    """Data of scale type. It can be base salary scale type, or allowance scale type.

    _name = 'ka_hr_payroll.scale.type'
    """

    _name = 'ka_hr_payroll.scale.type'

    code = fields.Char(string="Kode", size=3, required=True)
    name = fields.Char(string="Nama", size=64, required=True)

    _sql_constraints = [
        ('scale_type_unique', 'UNIQUE(code)', "Kode tipe skala sudah ada! Silakan menggunakan kode lainnya.")
    ]

class KaHrPayrollScale(models.Model):
    """Data of scale. It can be base salary scale, or allowance scale.

    _name = 'ka_hr_payroll.scale'
    """

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
        ('processed', "Diproses"),
    ], string="Status", default='draft')
    line_ids = fields.One2many('ka_hr_payroll.scale.lines', 'scale_id', readonly=True,
        states={'draft': [('readonly', False)]})

    @api.multi
    def name_get(self):
        """Override from `name_get()`. Representation name of model

        Decorators:
            api.multi

        Returns:
            List -- List of tuple of representation name
        """
        res = []
        for scale in self:
            res.append((scale.id, scale.date_start))
        return res

    @api.multi
    def action_draft(self):
        """Set state to `draft` then delete related lines

        Decorators:
            api.multi
        """
        self.state = 'draft'
        for line in self.line_ids:
            line.unlink()

    @api.multi
    def action_process(self):
        """Set state to `processed` then generate lines.

        Decorators:
            api.multi
        """
        self.state = 'processed'
        self.action_generate_lines()

    @api.multi
    def action_generate_lines(self):
        """Generate lines of this model
        """
        min_int = int(self.min_scale * 1000)
        max_int = int(self.max_scale * 1000)
        vs = self.value_start
        for i in range(min_int, max_int+1):
            self.env['ka_hr_payroll.scale.lines'].create({
                'scale_id': self.id,
                'scale': i * 0.001,
                'value': vs,
            })
            vs += self.delta

class KaHrPayrollScaleLines(models.Model):
    """Data lines of scale (detail skala).

    _name = 'ka_hr_payroll.scale.lines'
    """

    _name = 'ka_hr_payroll.scale.lines'

    scale_id = fields.Many2one('ka_hr_payroll.scale', string="Skala",
        required=True, ondelete='cascade')
    scale = fields.Float(string="Skala", digits=(6,3), required=True)
    value = fields.Float(string="Nilai", required=True)
