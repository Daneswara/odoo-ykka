from openerp import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseEditWizard(models.TransientModel):
    _name = "purchase.edit.wizard"
    
    @api.model
    def default_get(self, fields):
        res = super(PurchaseEditWizard,self).default_get(fields)
        active_id = self._context.get('active_id')
        if active_id:
            order_id = self.env['purchase.order'].browse(active_id)
            res['order_id'] = active_id
            res['new_date_planned'] = order_id.date_planned
        return res
    
    order_id = fields.Many2one('purchase.order', 'Surat Pesanan')
    new_date_planned = fields.Datetime('Ubah Ke Tanggal', required=True)
    reason = fields.Text('Alasan', required=True, default='Tanggal kedatangan barang diubah dengan alasan ...')
    
    @api.multi
    def do_edit_purchase(self):
        for this in self:
            this.order_id.write({'date_planned': this.new_date_planned, 'alasan': this.reason})
            self._cr.execute('update purchase_order_line set date_planned = %s where order_id = %s', (this.new_date_planned, this.order_id.id))
#             for line in this.order_id.order_line:
#                 line.write({'date_planned': this.new_date_planned})
            picking_ids = this.order_id.picking_ids
            # if PO direksi
            if this.order_id.order_type == 'rkout':
                source_uid  =  self.env.user.company_id.intercompany_user_id.id
                ou_company = this.order_id.sudo(source_uid).operating_unit_id.get_company_ref()[0]
                # search PO factory, then edit scheduled date PO, set picking_ids
                dest_order_src = self.env['purchase.order'].sudo(source_uid).with_context(company_id=ou_company).search([('source_order_id','=',this.order_id.id)])
                if dest_order_src:
                    dest_order_src.write({'date_planned': this.new_date_planned, 'alasan': this.reason})
                    for line2 in dest_order_src.order_line:
                        line2.write({'date_planned': this.new_date_planned})
                    picking_ids = dest_order_src.picking_ids
            # edit picking and stock move
            for picking in picking_ids:
                if picking.state not in ('cancel','done'):
                    picking.write({'min_date': this.new_date_planned})
                    for move in picking.move_lines:
                        move.write({'date_expected': this.new_date_planned})
                            
                            
                            