# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api

class KaHrPayrollEmployee(models.Model):
    """Master data of employee.

    _inherit = 'hr.employee'
    """

    _inherit = 'hr.employee'

    scale = fields.Float(string="Skala", digits=(6,3))
    gaji_pokok = fields.Float(string="Gaji Pokok", compute='_compute_gapok', store=True)

    @api.depends('scale')
    def _compute_gapok(self):
        """To compute gapok, depends of scale and golongan_id of employee.

        Decorators:
            api.depends('scale')
        """
        for employee in self:
            if not employee.scale:
                continue

            gapok_scale = self.env['ka_hr_payroll.gapok.scale'].search([
                ('date_start', '<=', fields.Date.today()),
                ('golongan_id', '=', employee.golongan_id.id),
                ('company_id', '=', employee.company_id.id),
            ], order='date_start desc', limit=1)

            if gapok_scale:
                gapok_scale_lines = self.env['ka_hr_payroll.gapok.scale.lines'].search([
                    ('gapok_scale_id', '=', gapok_scale.id),
                    ('scale', '=', employee.scale)
                ], limit=1)
                employee.gaji_pokok = gapok_scale_lines.value
