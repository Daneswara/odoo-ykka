# -*- coding: utf-8 -*-

from odoo import models, fields, api

class KaHrPayrollConfigWizard(models.TransientModel):
    _name = 'ka_hr_payroll.config.wizard'

    company_id = fields.Many2one('res.company', string="Unit/PG", required=True,
        default=lambda self: self.env.user.company_id)
    konjungtur = fields.Float(related='company_id.konjungtur', string="Konjungtur", required=True,
        default=1.0)
    
    @api.multi
    def save_data(self):
        self.company_id.konjungtur = self.konjungtur
