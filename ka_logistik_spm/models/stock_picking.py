from openerp import models, fields, api, _

class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    @api.multi
    def do_transfer(self):
        super(StockPicking,self).do_transfer()
        for this in self:
            if this.location_id.usage == 'supplier':
                pengajuan_ids = []
                for move in this.move_lines:
                    if move.spm_line_id and move.spm_line_id.pengajuan_id and move.spm_line_id.pengajuan_id.id not in pengajuan_ids:
                        pengajuan_ids.append(move.spm_line_id.pengajuan_id.id)
                        
                if pengajuan_ids != []:
                    for pengajuan_id in self.env['logistik.pengajuan.spm'].browse(pengajuan_ids):
                        products = ""
                        for move in this.move_lines:
                            if move.spm_line_id and move.spm_line_id.pengajuan_id and move.spm_line_id.pengajuan_id.id == pengajuan_id.id:
                                products += ('- ' + move.product_id.display_name + ' (' + str(move.product_uom_qty) + ' ' + move.product_uom.name + ')<br/>')
                        email = self.env.ref('ka_logistik_spm.template_incoming_product_notification')
                        base_template = email.body_html
                        content = '''%s'''%(email.body_html)
                        body_message = content%(products)
                        email.write({'body_html': body_message})
                        post_vars = {'message_type': 'notification', 
                                     'message_subtype': 'mt_comment',
                                     'partner_ids': [pengajuan_id.user_id.partner_id.id]}
                        pengajuan_id.message_post_with_template(email.id, **post_vars)
                        email.write({'body_html': base_template})
                    