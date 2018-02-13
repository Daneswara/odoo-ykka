from odoo import api, fields, models, _

class account_analytic_account(models.Model):
    _inherit = 'account.analytic.account'

    purchase_line_ids = fields.One2many('purchase.order.line', 'account_analytic_id', string='Realisasi SP', readonly=True)