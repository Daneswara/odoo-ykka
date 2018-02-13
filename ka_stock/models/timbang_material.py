from odoo import api, fields, models, _

class ka_timbang_material(models.Model):
    _inherit = "ka_timbang.material" 
     
    tank_id = fields.Many2one('stock.tank', 'Tangki')
    product_type = fields.Selection([("sugar", "Gula"),
                                     ("molasses", "Tetes"),
                                     ("bagasse", "Ampas"),
                                     ("other", "Lainnya")], string="Jenis Produk", track_visibility="always", copy=False)
    product_sugar_category = fields.Selection([("karung", "Karung"),
                                               ("retail", "Retail")], string="Kategori Produk", track_visibility="always", copy=False)
    
    
    @api.onchange('product_type')
    def onchage_product_type(self):
        if self.product_type == 'sugar':
            self.product_sugar_category = 'karung'
        elif self.product_type == 'molasses':
            self.product_id = self.env.user.company_id.product_molasses_id.id
        elif self.product_type == 'bagasse':
            self.product_id = self.env.user.company_id.product_bagasse_id.id   
    
    @api.onchange('product_sugar_category')
    def onchange_product_sugar_category(self):
        if self.product_sugar_category == 'karung':
            self.product_id =  self.env.user.company_id.product_sugar_id.id
        if self.product_sugar_category == 'retail':
            self.product_id =  self.env.user.company_id.product_sugar_retail_id.id
#         if self.product_sugar_category == 'premium':
#             self.product_id =  self.env.user.company_id.product_sugarpremium_id.id
    
    