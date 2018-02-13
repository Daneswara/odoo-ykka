from openerp import models, fields, api

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    account_pemakaian_barang = fields.Many2one("account.account", string="Pemakaian Barang", company_dependent=True)