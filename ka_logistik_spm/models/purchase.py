from odoo import models, fields, api, _

class purchase_order(models.Model):
    _inherit = "purchase.order"
    
    spm_id = fields.Many2one('logistik.spm', string='Nomor SPM')