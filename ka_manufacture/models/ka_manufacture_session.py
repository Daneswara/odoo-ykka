from odoo import models, fields, api
from datetime import datetime
from docutils.nodes import field
import datetime

class ManufactureSession(models.Model):
    _name = "ka_manufacture.session"
    _description = "Manufacture Session for PT Kebon Agung"
    _inherit = ['mail.thread']
    
    name = fields.Char(string="Name", default="New")
    fiscalyear_id = fields.Many2one("ka.account.fiscalyear", string="Fiscal Year")
    date_start = fields.Date(string="Mulai")
    date_end = fields.Date(string="Selesai")
    capacity = fields.Integer(string="Kapasitas")
    note = fields.Char(string="Keterangan")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id)
    state = fields.Selection([("draft", "Draft"),
                              ("open", "Open"),
                              ("close", "Close")],
                                string = "Status", default="draft", track_visibility="always")    
