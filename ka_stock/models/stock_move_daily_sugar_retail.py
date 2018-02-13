from odoo import models, fields, api
from datetime import datetime
import time
from odoo.exceptions import UserError

class StockMoveDailySugarRetail(models.Model):
    _name = "stock.move.daily.sugar.retail"
    _description = "Stock Move Daily Sugar Retail for PT Kebon Agung"
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'
    
    name = fields.Char(string="Name", default="New", copy=False)
    date = fields.Date(string="Tanggal", default=fields.Datetime.now)
    state = fields.Selection([("draft", "Draft"),
                              ("proposed", "Proposed"),
                              ("done", "Done")],
                                string = "Status", default="draft", track_visibility="always", copy=False)
    product_id = fields.Many2one("product.product", string="Product", default=lambda self: self.env.user.company_id.product_sugar_retail_id)
    product_qty = fields.Float("Quantity", copy=False)
    product_uom = fields.Many2one("product.uom", string="Unit of Measure")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id)
    move_ids = fields.One2many("stock.move", "move_daily_sugar_retail_id", string="Stock Moves", copy=False)
    manufacture_daily_id_sugar_retail = fields.Many2one("ka_manufacture.daily", string="Hari Giling")
    
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        self.product_uom = self.product_id.production_package_uom_id.id
        
    @api.multi
    def unlink(self):
        for this in self:
            if this.state != 'draft':
                raise UserError('Sorry, you cannot delete non-draft transaction.')
        return super(StockMoveDailySugarRetail, self).unlink()
    
    @api.multi
    def action_view_picking(self):
        for this in self:
            domain = [('id', 'in', [x.picking_id.id for x in self.env['stock.move'].search([('move_daily_sugar_retail_id','=', this.id)])])]

            return {
                'name': 'Stock Picking',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'domain' : domain,
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'target': 'current',  
            }
    
    @api.multi
    def propose_daily_sugar_retail_transaction(self):
        for this in self:
            this.write({'state' : 'proposed'})
        return True
    
    @api.multi
    def set_draft_daily_sugar_retail_transaction(self):
        for this in self:
            this.write({'state': 'draft'})
        return True
    
    @api.multi
    def validate_daily_sugar_retail_transaction(self):
        for this in self:
            line_item_stock = []
            vals = {'state': 'done'}
            if this.name == 'New':
                sequence_src = self.env['ir.sequence'].search([('name','=','Stock Move Daily Sugar Retail'),('company_id','=',self.env.user.company_id.id)], limit=1)
                if not sequence_src:
                    raise UserError('Penomoran untuk produksi harian gula retail belum ada. Silahkan hubungi Administrator.')
                vals['name'] = sequence_src.next_by_id()
            this.write(vals)
            
            data_entry = {}
            date_now = datetime.now().date()
            picking_type_id = self.env.user.company_id.picking_type_produce_id.id
            location_production_id = this.product_id.property_stock_production.id
            stock_picking_obj = self.env['stock.picking']
            
            vals_stock = {
                'product_id' : this.product_id.id,
                'product_uom_qty' : this.product_uom.factor_inv * this.product_qty,
                'product_uom' : this.product_id.uom_id.id,
                'name' : this.product_id.display_name,
                'picking_type_id' : picking_type_id, 
                'location_id' : location_production_id,
                'location_dest_id' : self.env.user.company_id.location_factory_id.id,
                'date_expected' : date_now,
                'move_daily_sugar_retail_id' : this.id
            }
            line_item_stock.append((0, 0, vals_stock))

            data_entry = {
                'location_id' : location_production_id,
                'location_dest_id' : self.env.user.company_id.location_factory_id.id,
                'min_date': date_now,
                'date_transfer': date_now,
                'origin': this.name,
                'move_lines': line_item_stock,
                'picking_type_id': picking_type_id,
            }

            stock_picking_create = stock_picking_obj.create(data_entry)
            stock_picking_create.action_confirm()
            stock_picking_create.do_transfer()
