from odoo import models, fields, api
from odoo.tools.float_utils import float_compare
    
class stock_move(models.Model):
    _inherit = "stock.move"
    
    move_daily_id = fields.Many2one("stock.move.daily.sugar", string="Stock Move Daily Sugar")
    move_daily_sugar_retail_id = fields.Many2one("stock.move.daily.sugar.retail", string="Stock Move Daily Sugar Retail")
#     move_daily_sugar_premium_id = fields.Many2one("stock.move.daily.sugar.premium", string="Stock Move Daily Sugar Premium")
    move_daily_molasses_id = fields.Many2one("stock.move.daily.molasses", string="Move Daily Molasses")
    move_daily_bagasse_id = fields.Many2one("stock.move.daily.bagasse", string="Move Daily Bagasse")