from odoo import models, fields, api, _


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'
    
    source_attachment_id = fields.Many2one('ir.attachment', 'Source Attachment')
    dest_attachment_id = fields.Many2one('ir.attachment', 'Destination Attachment')
    
    @api.model
    def create(self, values):
        res = super(IrAttachment, self).create(values)
        source_uid = self.env.user.company_id.intercompany_user_id.id
        
        if res.res_model == 'account.invoice': 
            inv_dest = False
            inv_source = self.env['account.invoice'].browse(res.res_id)
    
            if inv_source.dest_invoice_id:
                inv_dest = self.env['account.invoice'].sudo(source_uid).search([('id','=', inv_source.dest_invoice_id.id)])
            elif inv_source.source_invoice_id:
                inv_dest = self.env['account.invoice'].sudo(source_uid).search([('id','=', inv_source.source_invoice_id.id)])
            
            if inv_dest:
                default = {
                        'company_id': inv_dest.company_id.id,
                        'name': values.get('name'),
                        'res_id': inv_dest.id,
                        'res_model': values.get('res_model'),
                        'source_attachment_id': res.id
                    }

                if self._context.get('has_copy') != False:
                    copy_att = res.sudo(source_uid).with_context(has_copy=False).copy(default=default)
                    res.write({'dest_attachment_id': copy_att.id})
        return res
    
    @api.multi
    def unlink(self):
        for this in self:
            source_uid = self.env.user.company_id.intercompany_user_id.id

            if this.res_model == "account.invoice" and self._context.get('has_copy') != False:
                if this.source_attachment_id:
                    inv = self.env['ir.attachment'].sudo(source_uid).browse(this.source_attachment_id.id)
                    inv.sudo(source_uid).with_context(has_copy=False).unlink()
                elif this.dest_attachment_id:
                    inv = self.env['ir.attachment'].sudo(source_uid).browse(this.dest_attachment_id.id)
                    inv.sudo(source_uid).with_context(has_copy=False).unlink()
        return super(IrAttachment, self).unlink()