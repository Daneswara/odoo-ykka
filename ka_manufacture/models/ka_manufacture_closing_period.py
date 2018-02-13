from odoo import models, fields, api
from datetime import datetime
from docutils.nodes import field
import datetime

class ManufactureClosingPeriod(models.Model):
    _name = "ka_manufacture.closing.period"
    _description = "Manufacture Closing Period for PT Kebon Agung"
    _inherit = ['mail.thread']
    
    name = fields.Char(string="Name", default="New")
    code = fields.Char("Kode", digit=5)
    session_id = fields.Many2one("ka_manufacture.session", string="Session")
    date_start = fields.Date(string="Tanggal Awal")
    date_end = fields.Date(string="Tanggal Akhir")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id)
    state = fields.Selection([("draft", "Draft"),
                              ("open", "Open"),
                              ("close", "Close")],
                                string = "Status", default="draft", track_visibility="always")    

