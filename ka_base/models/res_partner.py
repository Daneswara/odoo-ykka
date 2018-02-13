from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    is_operating_unit = fields.Boolean("Sebagai Unit/PG", default=False)
    
    @api.one
    def get_company_ref(self):
        company  = self.env['res.company'].search([('partner_id', '=', self.id)])
        return company
    