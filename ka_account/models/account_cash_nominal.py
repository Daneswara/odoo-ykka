from odoo import models, fields, api
from odoo.exceptions import UserError
from pygments.lexer import _inherit

class AccountCashNominal(models.Model):
    _name = "account.cash.nominal"
    _order = "sequence asc"
    _description = "Account Cash Nominal for Count on Bank Statement"
    
    name = fields.Char(string="Name")
    sequence = fields.Integer("Sequence")
    value = fields.Float(string="Nominal")
    is_cash = fields.Boolean('Cash', default=True)
    

class AccountCashboxLine(models.Model):
    _inherit = "account.cashbox.line"
    _order = "cash_nominal_id desc"
    
    cash_nominal_id = fields.Many2one("account.cash.nominal", string="Cash Nominal")
    number_cashier = fields.Integer('Lembar Kasir')
    
    @api.one
    @api.depends('coin_value', 'number', 'number_cashier')
    def _sub_total(self):
        """ Calculates Sub total"""
        self.subtotal = self.coin_value * (self.number + self.number_cashier)
