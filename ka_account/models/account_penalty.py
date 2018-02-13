from openerp import models, fields, api
from datetime import datetime
import pytz

class AccountPenalty(models.Model):
    _name = "account.penalty"
    _description = "Account Penalty for Overdue Shipping"

    invoice_id = fields.Many2one("account.invoice", string="Invoice")
    product_id = fields.Many2one("product.product", string="Product")
    amount = fields.Monetary(string="Nilai Denda")
    due_date = fields.Date(string="Tanggal Batas")
    penalty_date = fields.Date(string="Tanggal Terima")
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id', store=True)

    
class AccountPenaltyConfig(models.Model):
    _name = "account.penalty.config"
    _description = "Configuration for Account Penalty"
    
    min_days = fields.Integer(string="Min Days")
    max_days = fields.Integer(string="Max Days")
    percent_penalty = fields.Float(string="Penalty (%)")
    
