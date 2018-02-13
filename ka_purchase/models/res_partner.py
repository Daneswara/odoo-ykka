# -*- coding: utf-8 -*-
import time
from odoo import models, fields, api
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    account_investasi_baru = fields.Many2one('account.account', string='Investasi Baru', company_dependent=True)
    account_perbaikan_luar_biasa = fields.Many2one('account.account', string='Perbaikan Luar Biasa', company_dependent=True)
    account_inventaris = fields.Many2one('account.account', string='Inventaris', company_dependent=True)
    status_transaksi = fields.Char(compute='_compute_status_transaksi', string='Status Transaksi')

    @api.multi
    def _compute_status_transaksi(self):
        for s in self:
#             s.status_transaksi = 'Transaksi Pasif' if not s.no_acc and not s.is_calon and s.purchase_order_count <= 0 else ''
            s.status_transaksi = 'Transaksi Pasif' if s.bank_account_count <= 0 else ''
    
class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    
    @api.model
    def default_get(self, fields):
        res = super(ResPartnerBank,self).default_get(fields)
        res['company_id'] = False
        return res
    
    @api.depends('acc_number')
    def _compute_sanitized_acc_number(self):
        for bank in self:
            bank.sanitized_acc_number = bank.acc_number