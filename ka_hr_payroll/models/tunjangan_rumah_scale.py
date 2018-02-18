# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api

class KaHrPayrollTunjanganRumahScale(models.Model):
    """Data of home allowance scale (skala tunjangan rumah).

    _name = 'ka_hr_payroll.tunjangan.rumah.scale'
    """

    _name = 'ka_hr_payroll.tunjangan.rumah.scale'

    date_start = fields.Date(string="Tanggal Mulai", required=True, default=fields.Date.today)
    min_scale = fields.Float(string="Skala Awal", required=True, default=1.000)
    max_scale = fields.Float(string="Skala Akhir", required=True, default=1.000)
    value_start = fields.Float(string="Nilai Awal", required=True)
    delta = fields.Float(string="Nilai Delta", required=True)
    golongan_id = fields.Many2one(string="Golongan", required=True)
    company_id = fields.Many2one('res.company', string="Unit/PG", required=True,
        default=lambda self: self.env.user.company_id)
    line_ids = fields.One2many('ka_hr_payroll.tunjangan.rumah.scale.lines', 'gapok_scale_id')

    @api.multi
    def action_generate_lines(self):
        """Generate lines of this model

        Decorators:
            api.multi
        """
        min_int = int(self.min_scale * 1000)
        max_int = int(self.max_scale * 1000)
        vs = self.value_start
        for i in range(min_int, max_int+1):
            self.env['ka_hr_payroll.tunjangan.rumah.scale.lines'].create({
                'tunjangan_scale_id': self.id,
                'scale': i * 0.001,
                'value': vs,
            })
            vs += self.delta

class KaHrPayrollTunjanganRumahScaleLines(models.Model):
    """Data lines of home allowance scale (detail skala tunjangan rumah).

    _name = 'ka_hr_payroll.tunjangan.rumah.scale.lines'
    """

    _name = 'ka_hr_payroll.tunjangan.rumah.scale.lines'

    tunjangan_scale_id = fields.Many2one('ka_hr_payroll.tunjangan.rumah.scale', string="Skala Tunjangan Rumah", required=True)
    scale = fields.Float(string="Skala", required=True)
    value = fields.Float(string="Nilai", required=True)
