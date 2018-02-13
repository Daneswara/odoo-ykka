from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    production_uom_id = fields.Many2one("product.uom", string="Production UoM")
    production_package_uom_id = fields.Many2one("product.uom", string="Production Package UoM")
    
    @api.model
    def default_get(self, fields):
        res = super(ProductTemplate, self).default_get(fields)
        res['type'] = 'product'
        return res