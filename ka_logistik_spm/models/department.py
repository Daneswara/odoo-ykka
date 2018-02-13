from odoo import api, fields, models

class Department(models.Model):
    _inherit = "hr.department"

    
    sequence_id = fields.Many2one('ir.sequence', string="Nomor Urut SPM")
    is_department = fields.Boolean('Department')