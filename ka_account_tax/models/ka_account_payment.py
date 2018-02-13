from odoo import api, fields, models, _

class KaAccountVendorPayment(models.Model):
    _inherit = "ka_account.payment"        
    
    pph_ids = fields.One2many('ka_account.payment.pph', 'payment_id', 'PPh')
    amount_pph = fields.Monetary(string='PPh', compute='_compute_amount_pph', store=True)
    
    @api.depends('pph_ids.amount')
    def _compute_amount_pph(self):
        for rec in self:
            rec.amount_pph = sum([tax.amount for tax in rec.pph_ids])
    
class KaAccountPayableTaxes(models.Model):
    _name = 'ka_account.payment.pph'
    _description = 'Potongan PPh Supplier'
    
    payment_id = fields.Many2one('ka_account.payment', string='Tagihan Supplier', required=True)
    tax_id = fields.Many2one('account.tax', string='Jenis Pajak', required=True)
    tax_rate = fields.Float(related='tax_id.amount', string='Tarif(%)')
    amount = fields.Monetary('Jumlah', compute='_compute_pph', store=True)
    currency_id = fields.Many2one('res.currency', string='Account Currency')
    
    @api.multi
    @api.depends('tax_id', 'payment_id.amount_dpp')
    def _compute_pph(self):
        for rec in self:
            rec.amount = (rec.payment_id.amount_dpp * rec.tax_rate) / 100
    