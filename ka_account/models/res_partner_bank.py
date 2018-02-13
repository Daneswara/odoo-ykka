from odoo import fields, api, models, _

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    _order = "bank_name asc, priority asc"
    
    priority = fields.Integer('Priority', default=1)
    
    @api.multi
    @api.depends('bank_id')
    def name_get(self):
        result = []
        for bank in self:
            name = bank.bank_id.name
            result.append((bank.id, name))
        return result
    