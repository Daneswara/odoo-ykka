# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
import pytz

class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    @api.multi
    def process(self):
        self.ensure_one()
        # PENGELUARAN BARANG
        if self.pick_id.using_analytic_pkrat and self.pick_id.state != 'assigned':
            raise UserError('Validasi Gagal! Beberapa kuantum produk yang diminta tidak tersedia.')
        # If still in draft => confirm and assign
        if self.pick_id.state == 'draft':
            self.pick_id.action_confirm()
            if self.pick_id.state != 'assigned':
                self.pick_id.action_assign()
                if self.pick_id.state != 'assigned':
                    raise UserError(_("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
        for pack in self.pick_id.pack_operation_ids:
            if pack.product_qty > 0:
                pack.write({'qty_done': pack.product_qty})
            else:
                pack.unlink()
        # additional by PAA : journal date based on date of transfer
        user = self.env.user
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        date_transfer = datetime.strptime(self.pick_id.date_transfer, '%Y-%m-%d %H:%M:%S')
        date_transfer = pytz.utc.localize(date_transfer).astimezone(tz)
        date_transfer = datetime.strftime(date_transfer, '%Y-%m-%d')
        self.with_context(force_period_date = date_transfer).pick_id.do_transfer()
