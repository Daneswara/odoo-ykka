from odoo import models, fields, api, _

class ManufactureDaily(models.Model):
    _inherit = "ka_manufacture.daily"
    
    sugar_production_ids = fields.One2many("stock.move.daily.sugar", "manufacture_daily_id_sugar", string="Produksi Gula")
#     sugarpremium_production_ids = fields.One2many("stock.move.daily.sugar.premium", "manufacture_daily_id_sugarpremium", string="Produksi Gula Premium")
    sugar_retail_production_ids = fields.One2many("stock.move.daily.sugar.retail", "manufacture_daily_id_sugar_retail", string="Produksi Gula Retail")
    molasses_production_ids = fields.One2many("stock.move.daily.molasses", "manufacture_daily_id_molasses", string="Produksi Tetes")
    bagasse_production_ids = fields.One2many("stock.move.daily.bagasse", "manufacture_daily_id_bagasse", string="Produksi Ampas")
    qty_sugar = fields.Float("Produksi Gula Karung - Kg", compute="get_total_qty")
    qty_sugar_retail = fields.Float("Produksi Gula Retail - Kg", compute="get_total_qty")
#     qty_sugar_premium = fields.Float("Produksi Gula Premium - Kg", compute="get_total_qty")
    qty_molasses = fields.Float("Produksi Tetes - Kg", compute="get_total_qty")
    qty_bagasse = fields.Float("Produksi Ampas - Kg", compute="get_total_qty")
    
    @api.multi
    @api.depends('sugar_production_ids.total_production_qty','molasses_production_ids.total_qty', 'bagasse_production_ids.product_qty')
    def get_total_qty(self):
        for this in self:
            total_sugar = 0
            total_sugar_retail = 0
#             total_sugar_premium = 0
            total_molasses = 0
            total_bagasse = 0
            for sugar in this.sugar_production_ids:
                total_sugar += (sugar.total_production_qty * sugar.product_uom.factor_inv)
            this.qty_sugar = total_sugar
            
            for sugar_retail in this.sugar_retail_production_ids:
                total_sugar_retail += sugar_retail.product_qty 
            this.qty_sugar_retail = total_sugar_retail
            
#             for sugar_premium in this.sugarpremium_production_ids:
#                 total_sugar_premium += sugar_premium.product_qty
#             this.qty_sugar_premium = total_sugar_premium
            
            for molasses in this.molasses_production_ids:
                total_molasses += molasses.total_qty
            this.qty_molasses = total_molasses
            
            for bagasse in this.bagasse_production_ids:
                total_bagasse += bagasse.product_qty
            this.qty_bagasse = total_bagasse
            
            