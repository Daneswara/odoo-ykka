from openerp import models, fields, api
    
class AccountConfigSettings(models.TransientModel):
    _inherit = "account.config.settings"
    
    @api.one
    @api.depends('company_id')
    def _compute_price_kontrak_a(self):
        self.default_price_contract_a = self.company_id.default_price_contract_a
    
    @api.one
    def _set_price_kontrak_a(self):
        if self.default_price_contract_a != self.company_id.default_price_contract_a:
            self.company_id.default_price_contract_a = self.default_price_contract_a
            
    default_price_contract_a = fields.Monetary(string="Default Price Kontrak A", compute="_compute_price_kontrak_a", inverse="_set_price_kontrak_a")

class ResCompany(models.Model):
    _inherit = "res.company"
    
    default_price_contract_a = fields.Monetary(string="Default Price Kontrak A")