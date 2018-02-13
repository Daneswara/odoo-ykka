from odoo import models, fields, api, _

class res_partner(models.Model):
    _inherit = "res.partner"
    
    @api.model
    def default_get(self, fields):
        res = super(res_partner,self).default_get(fields)
        lang_src = self.env['res.lang'].search([('code','=','id_ID')])
        if lang_src:
            res['lang'] = 'id_ID'
        return res
    
    sale_product_ids = fields.Many2many('ka_sale.order.category', 'partner_sale_order_categ_rel', 'partner_id', 'so_categ_id', 'Kategori SO')