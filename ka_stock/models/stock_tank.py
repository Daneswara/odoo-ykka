from odoo import models, fields, api
from datetime import datetime
from docutils.nodes import field
import datetime
from odoo.exceptions import UserError

class StockTank(models.Model):
    _name = "stock.tank"
    _description = "Stock Tank for PT Kebon Agung"
    
    name = fields.Char("Name")
    capacity = fields.Float("Max Capacity (Kg)")
    current_brix = fields.Float("Current Brix (%)")
    current_temperature = fields.Float("Current Temperature")