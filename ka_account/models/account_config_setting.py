from openerp import models, fields, api
from datetime import datetime
import pytz

class AccountConfigSettings(models.TransientModel):
    _inherit = "account.config.settings"
    
    @api.one
    @api.depends('company_id')
    def _compute_account_penalty(self):
        self.penalty_account_id = self.company_id.penalty_account_id
    
    @api.one
    def _set_account_penalty(self):
        if self.penalty_account_id != self.company_id.penalty_account_id:
            self.company_id.penalty_account_id = self.penalty_account_id
            
    penalty_account_id = fields.Many2one("account.account", string="Penalty Account", compute="_compute_account_penalty", inverse="_set_account_penalty")
    
    @api.one
    @api.depends('company_id')
    def _compute_pph(self):
        self.default_pph_account_id = self.company_id.default_pph_account_id
    
    @api.one
    def _set_account_pph(self):
        if self.default_pph_account_id != self.company_id.default_pph_account_id:
            self.company_id.default_pph_account_id = self.default_pph_account_id
    
    default_pph_account_id = fields.Many2one("account.account", string="Default Account PPh", compute="_compute_pph", inverse="_set_account_pph")
    
    @api.one
    @api.depends('company_id')
    def _compute_bail(self):
        self.default_bail_account_id = self.company_id.default_bail_account_id
    
    @api.one
    def _set_account_bail(self):
        if self.default_bail_account_id != self.company_id.default_bail_account_id:
            self.company_id.default_bail_account_id = self.default_bail_account_id
    
    default_bail_account_id = fields.Many2one("account.account", string="Default Account Garansi", compute="_compute_bail", inverse="_set_account_bail")
    
    @api.one
    @api.depends('company_id')
    def _compute_account_int_tranfer(self):
        self.default_account_internal_transfer = self.company_id.default_account_internal_transfer
    
    @api.one
    def _set_account_int_tranfer(self):
        if self.default_account_internal_transfer != self.company_id.default_account_internal_transfer:
            self.company_id.default_account_internal_transfer = self.default_account_internal_transfer
            
    default_account_internal_transfer = fields.Many2one("account.account", string="Default Account Internal Transfer", compute="_compute_account_int_tranfer", inverse="_set_account_int_tranfer")
    
#     @api.one
#     @api.depends('company_id')
#     def _compute_percent_pph(self):
#         self.default_percent_pph = self.company_id.default_percent_pph
#     
#     @api.one
#     def _set_percent_pph(self):
#         if self.default_percent_pph != self.company_id.default_percent_pph:
#             self.company_id.default_percent_pph = self.default_percent_pph
#     
#     default_percent_pph = fields.Float(string ="Percent PPH (%)", compute="_compute_percent_pph", inverse="_set_percent_pph")

class ResCompany(models.Model):
    _inherit = "res.company"
    
    penalty_account_id = fields.Many2one("account.account", string="Penalty Account")
    default_pph_account_id = fields.Many2one("account.account", string="PPh Account")
    default_bail_account_id = fields.Many2one("account.account", string= "Bail Account")
    default_account_internal_transfer = fields.Many2one("account.account", string= "Default Account Internal Transfer")
#     default_percent_pph = fields.Float(string= "Percent PPH (%)")