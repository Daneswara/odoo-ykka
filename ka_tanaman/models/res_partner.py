from odoo import fields, models

class Partner(models.Model):
    _inherit = 'res.partner'


    kud = fields.Boolean("Kud",default=False)
    farmer= fields.Boolean("Petani",default=False)