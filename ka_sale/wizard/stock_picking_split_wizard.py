from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class stock_picking_split_wizard(models.TransientModel):
    _name = "stock.picking.split.wizard"
    
    @api.model
    def default_get(self, fields):
        res = super(stock_picking_split_wizard,self).default_get(fields)
        picking_id = self._context.get('active_id', False)
        picking_vals = []
        for picking in self.env['stock.picking'].browse(picking_id):
            for move in picking.move_lines:
                picking_vals.append((0,0,{'product_qty': move.product_uom_qty,
                                          'agent_partner_id': picking.agent_partner_id.id or False,
                                          'delivery_number': picking.delivery_number,
                                          'timbangan_id': picking.timbangan_id.id or False}))
                res['move_id'] = move.id
                res['product_id'] = move.product_id.id
                res['product_uom'] = move.product_uom.id
                res['total_qty'] = move.product_uom_qty
                break
        res['picking_id'] = picking_id
        res['split_lines'] = picking_vals
        return res
    
    picking_id = fields.Many2one('stock.picking', 'Stock Move')
    move_id = fields.Many2one('stock.move', "Stock Move")
    split_lines = fields.One2many('stock.picking.split.wizard.line', 'split_id', 'Split Lines')
    product_id = fields.Many2one('product.product', 'Product')
    product_uom = fields.Many2one('product.uom', 'Unit of Measure')
    total_qty = fields.Float('Total Quantity')
    
    @api.multi
    def do_split_stock_picking(self):
        for this in self:
            res_pickings = []
            total_line_qty = 0.0
            for line in this.split_lines:
                picking_id = this.picking_id.copy({'timbangan_id': line.timbangan_id.id,
                                                   'agent_partner_id': line.agent_partner_id.id,
                                                   'delivery_number': line.delivery_number,
                                                   'move_lines': None})
                this.move_id.copy({'picking_id': picking_id.id,
                                   'product_uom_qty': line.product_qty})
                picking_id.action_confirm()
                picking_id.action_assign()
                res_pickings.append(picking_id.id)
                total_line_qty += line.product_qty
            # compute rest qty
            rest_qty = this.total_qty -  total_line_qty
            if rest_qty > 0:
                this.picking_id.do_unreserve()
                this.picking_id.write({'timbangan_id': False, 'delivery_number': False})
                this.move_id.write({'product_uom_qty': rest_qty})
                this.picking_id.action_assign()
                res_pickings.append(this.picking_id.id)
            else:
                this.picking_id.action_cancel()
                for move in this.picking_id.move_lines:
                    move.unlink()
                for packop in this.picking_id.pack_operation_product_ids:
                    packop.unlink()
                this.picking_id.unlink()
            return {
                'name':'Stock Pickings',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window',
                'domain': [('id','in',res_pickings)],
                'target': 'current'
            }
                
    
class stock_picking_split_wizard_line(models.TransientModel):
    _name = "stock.picking.split.wizard.line"
    
    split_id = fields.Many2one('stock.picking.split.wizard', 'Picking Split')
    product_qty = fields.Float('Quantity')
    agent_partner_id = fields.Many2one('res.partner', string="Agen", domain=[('company_type', '=', 'person')])
    delivery_number = fields.Char('No. Kirim')
    timbangan_id = fields.Many2one('ka_timbang.material', 'No. Timbangan')
    
    @api.onchange('timbangan_id')
    def _onchange_timbangan_id(self):
        self.product_qty = self.timbangan_id.weight_net
    
    