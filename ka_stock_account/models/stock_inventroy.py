from odoo import api, fields, models, _

class StockInventory(models.Model):
    _inherit = "stock.inventory"
    
    def default_location_id(self):
        res = False
        warehouse_src = self.env['stock.warehouse'].search([('company_id','=',self.env.user.company_id.id)], limit=1)
        if warehouse_src:
            res = warehouse_src.lot_stock_id.id
        return res
    
    location_id = fields.Many2one(
        'stock.location', 'Inventoried Location',
        readonly=True, required=True,
        states={'draft': [('readonly', False)]}, default=default_location_id)