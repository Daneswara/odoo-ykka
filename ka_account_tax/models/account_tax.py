from odoo import api, fields, models, _

class KaAccountTax(models.Model):
    _inherit = "account.tax"        
    
    is_pph = fields.Boolean('PPh')
    formulir_ref = fields.Char('Kode Formulir', help='Kode Formulir dari DPJ misal, F.1.1.33.04 -> F113304. Kode ini fungsinya pada saat Export CSV')
    
    