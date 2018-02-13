# -*- coding: utf-8 -*-

from odoo import fields, api, models, _

class AccountFinanacialReport(models.Model):
    _inherit = "account.financial.report"
    
    code = fields.Char(string="Kode", size=5)
    display_value = fields.Boolean('Display Value', compute='get_display_value')
    is_cashflow = fields.Boolean('Cashflow Report?')  
    cashflow_type = fields.Selection([
        ('ob', 'Saldo Awal'),
        ('in', 'Penerimaan'),
        ('out', 'Pengeluaran'),
        ('bl', 'Balance'),
        ], string='Move Type')
        
    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.parent_id:
                name = "%s / %s" % (record.parent_id.name_get()[0][1], name)
            result.append((record.id, name))
        return result

    @api.multi
    @api.depends('parent_id')
    def get_display_value(self):
        for this in self:
            res = True
            children_src = self.env['account.financial.report'].search([('parent_id','=',this.id)])
            if children_src:
                res = False
            this.display_value = res