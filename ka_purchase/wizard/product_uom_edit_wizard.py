from odoo import models, fields, api

class ProductUomEditWizard(models.TransientModel):
    _name = "product.uom.edit.wizard"
    
    @api.model
    def default_get(self, fields):
        res = super(ProductUomEditWizard,self).default_get(fields)
        active_model = self._context.get('active_model')
        active_id = self._context.get('active_id')
        if active_model:
            if active_model == 'product.template':
                res['product_tmpl_id'] = active_id
            elif active_model == 'product.product':
                res['product_id'] = active_id
            data_src = self.env[active_model].browse(active_id)
            if data_src:
                res['uom_id'] = data_src.uom_id.id
        return res
    
    
    product_id = fields.Many2one('product.product', 'Produk')
    product_tmpl_id = fields.Many2one('product.template', 'Produk')
    uom_id = fields.Many2one('product.uom', 'Satuan', required=True)
    
    
    @api.multi
    def do_edit_product_uom(self):
        for this in self:
            active_model = self._context.get('active_model')
            product_tmpl_id = False
            if active_model == 'product.template':
                product_tmpl_id = this.product_tmpl_id.id
            elif active_model == 'product.product':
                product_tmpl_id = this.product_id.product_tmpl_id.id
            # if product not empty
            if product_tmpl_id:
                self._cr.execute('update product_template set uom_id=%s, uom_po_id=%s where id=%s',
                                 (this.uom_id.id, this.uom_id.id, product_tmpl_id))
                # change data stock moves and PO line
                st_move_src = self.env['stock.move'].search([('product_id.product_tmpl_id','=',product_tmpl_id),
                                                             ('picking_id.state','not in',('done','cancel'))])
                for move in st_move_src:
                    self._cr.execute('update stock_move set product_uom=%s where id=%s',(this.uom_id.id, move.id))
                    if move.purchase_line_id:
                        self._cr.execute('update purchase_order_line set product_uom=%s where id=%s',(this.uom_id.id, move.purchase_line_id.id))
                # change data pack operation
                packop_src = self.env['stock.pack.operation'].search([('product_id.product_tmpl_id','=',product_tmpl_id),
                                                                      ('picking_id.state','not in',('done','cancel'))])
                for packop in packop_src:
                    self._cr.execute('update stock_pack_operation set product_uom_id=%s where id=%s',(this.uom_id.id, packop.id))
                
                
                    