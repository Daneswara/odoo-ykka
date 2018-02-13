from odoo import models, fields, api, _

class stock_config_settings(models.TransientModel):
    _inherit = "stock.config.settings"
    
    @api.one
    @api.depends('company_id')
    def get_receiving_production_info(self):
        self.product_sugar_id = self.company_id.product_sugar_id
#         self.product_sugarpremium_id = self.company_id.product_sugarpremium_id
        self.product_sugar_retail_id = self.company_id.product_sugar_retail_id
        self.product_molasses_id = self.company_id.product_molasses_id
        self.product_bagasse_id = self.company_id.product_bagasse_id
        self.picking_type_produce_id = self.company_id.picking_type_produce_id
        self.picking_type_factory_id = self.company_id.picking_type_factory_id
        self.picking_type_farmer_id = self.company_id.picking_type_farmer_id
        self.picking_type_natura_id = self.company_id.picking_type_natura_id
        self.location_production_dest_id = self.company_id.location_production_dest_id
        self.location_factory_id = self.company_id.location_factory_id
        self.location_farmer_id = self.company_id.location_farmer_id
        self.location_natura_id = self.company_id.location_natura_id
        self.percentage_bagi_hasil_non_natura = self.company_id.percentage_bagi_hasil_non_natura
        self.percentage_bagi_hasil_natura = self.company_id.percentage_bagi_hasil_natura
    
    @api.one
    def set_receiving_production_info(self):
        if self.product_sugar_id != self.company_id.product_sugar_id:
            self.company_id.product_sugar_id = self.product_sugar_id
#         if self.product_sugarpremium_id != self.company_id.product_sugarpremium_id:
#             self.company_id.product_sugarpremium_id = self.product_sugarpremium_id
        if self.product_sugar_retail_id != self.company_id.product_sugar_retail_id:
            self.company_id.product_sugar_retail_id = self.product_sugar_retail_id
        if self.product_molasses_id != self.company_id.product_molasses_id:
            self.company_id.product_molasses_id = self.product_molasses_id
        if self.product_bagasse_id != self.company_id.product_bagasse_id:
            self.company_id.product_bagasse_id = self.product_bagasse_id
        if self.picking_type_produce_id != self.company_id.picking_type_produce_id:
            self.company_id.picking_type_produce_id = self.picking_type_produce_id
        if self.picking_type_factory_id != self.company_id.picking_type_factory_id:
            self.company_id.picking_type_factory_id = self.picking_type_factory_id
        if self.picking_type_farmer_id != self.company_id.picking_type_farmer_id:
            self.company_id.picking_type_farmer_id = self.picking_type_farmer_id
        if self.picking_type_natura_id != self.company_id.picking_type_natura_id:
            self.company_id.picking_type_natura_id = self.picking_type_natura_id
        if self.location_production_dest_id != self.company_id.location_production_dest_id:
            self.company_id.location_production_dest_id = self.location_production_dest_id
        if self.location_factory_id != self.company_id.location_factory_id:
            self.company_id.location_factory_id = self.location_factory_id
        if self.location_farmer_id != self.company_id.location_farmer_id:
            self.company_id.location_farmer_id = self.location_farmer_id
        if self.location_natura_id != self.company_id.location_natura_id:
            self.company_id.location_natura_id = self.location_natura_id
        if self.percentage_bagi_hasil_non_natura != self.company_id.percentage_bagi_hasil_non_natura:
            self.company_id.percentage_bagi_hasil_non_natura = self.percentage_bagi_hasil_non_natura
        if self.percentage_bagi_hasil_natura != self.company_id.percentage_bagi_hasil_natura:
            self.company_id.percentage_bagi_hasil_natura = self.percentage_bagi_hasil_natura
            
    product_sugar_id = fields.Many2one('product.product', 'Product Sugar (Karung)', compute='get_receiving_production_info', inverse='set_receiving_production_info')
#     product_sugarpremium_id = fields.Many2one('product.product', 'Product Sugar (Premium)', compute='get_receiving_production_info', inverse='set_receiving_production_info')
    product_sugar_retail_id = fields.Many2one('product.product', 'Product Sugar (Retail)', compute='get_receiving_production_info', inverse='set_receiving_production_info')
    product_molasses_id = fields.Many2one('product.product', 'Product Molasses', compute='get_receiving_production_info', inverse='set_receiving_production_info')
    product_bagasse_id = fields.Many2one('product.product', 'Product Bagasse', compute='get_receiving_production_info', inverse='set_receiving_production_info')
    picking_type_produce_id = fields.Many2one('stock.picking.type', 'Production Operation Type', compute='get_receiving_production_info', inverse='set_receiving_production_info')
    picking_type_factory_id = fields.Many2one('stock.picking.type', 'Factory Operation Type', compute='get_receiving_production_info', inverse='set_receiving_production_info')
    picking_type_farmer_id = fields.Many2one('stock.picking.type', 'Farmer Operation Type', compute='get_receiving_production_info', inverse='set_receiving_production_info')
    picking_type_natura_id = fields.Many2one('stock.picking.type', 'Natura Operation Type', compute='get_receiving_production_info', inverse='set_receiving_production_info')
    location_production_dest_id = fields.Many2one('stock.location', 'Receiving Production Location', compute='get_receiving_production_info', inverse='set_receiving_production_info')
    location_factory_id = fields.Many2one('stock.location', 'Factory Location', compute='get_receiving_production_info', inverse='set_receiving_production_info')
    location_farmer_id = fields.Many2one('stock.location', 'Farmer Location', compute='get_receiving_production_info', inverse='set_receiving_production_info')
    location_natura_id = fields.Many2one('stock.location', 'Natura Location', compute='get_receiving_production_info', inverse='set_receiving_production_info')
    percentage_bagi_hasil_non_natura= fields.Float('Percentage Bagi Hasil Non-Natura', compute='get_receiving_production_info', inverse='set_receiving_production_info')
    percentage_bagi_hasil_natura = fields.Float('Percentage Bagi Hasil Natura', compute='get_receiving_production_info', inverse='set_receiving_production_info')
  
 
class res_company(models.Model):
    _inherit = "res.company"
    
    product_sugar_id = fields.Many2one('product.product', 'Product Sugar (Karung)')
#     product_sugarpremium_id = fields.Many2one('product.product', 'Product Sugar (Premium)')
    product_sugar_retail_id = fields.Many2one('product.product', 'Product Sugar (Retail)')
    product_molasses_id = fields.Many2one('product.product', 'Product Molasses')
    product_bagasse_id = fields.Many2one('product.product', 'Product Bagasse')
    picking_type_produce_id = fields.Many2one('stock.picking.type', 'Production Operation Type')
    picking_type_factory_id = fields.Many2one('stock.picking.type', 'Factory Operation Type')
    picking_type_farmer_id = fields.Many2one('stock.picking.type', 'Farmer Operation Type')
    picking_type_natura_id = fields.Many2one('stock.picking.type', 'Natura Operation Type')
    location_production_dest_id = fields.Many2one('stock.location', 'Receiving Production Location')
    location_factory_id = fields.Many2one('stock.location', 'Factory Location')
    location_farmer_id = fields.Many2one('stock.location', 'Farmer Location')
    location_natura_id = fields.Many2one('stock.location', 'Natura Location')
    percentage_bagi_hasil_non_natura = fields.Float('Percentage Bagi Hasil Non-Natura')
    percentage_bagi_hasil_natura = fields.Float('Percentage Bagi Hasil Natura')
    