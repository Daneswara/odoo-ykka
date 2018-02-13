from odoo import api, fields, models, _
        
class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    @api.multi
    def do_transfer(self):
        super(StockPicking, self).do_transfer()
        # check for return to supplier, will create new picking (supplier -> input)
        for this in self:
            if this.picking_code_type == 'incoming' and this.is_return_picking == True and this.location_dest_id.usage == 'supplier':
                origin_picking = False
                for move in this.move_lines:
                    if move.origin_returned_move_id:
                        origin_picking = move.origin_returned_move_id.picking_id
                        break
                if origin_picking:
                    new_picking = origin_picking.copy({'move_lines': []})
                    for move in this.move_lines:
                        origin_move = move.origin_returned_move_id
                        new_move = move.copy({'move_dest_id': origin_move.move_dest_id.id, 
                                              'picking_id': new_picking.id,
                                              'state': 'draft',
                                              'location_id': origin_move.location_id.id,
                                              'location_dest_id': origin_move.location_dest_id.id,
                                              'picking_type_id': origin_move.picking_type_id.id,
                                              'warehouse_id': origin_move.warehouse_id.id,
                                              'procure_method': origin_move.procure_method,
                                              'origin_returned_move_id': False})
                        new_move.write({'purchase_line_id': origin_move.purchase_line_id.id})
                    new_picking.action_confirm()
                    