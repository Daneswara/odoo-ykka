from odoo import models, fields, api
from odoo.exceptions import UserError

class logistik_edit_jenis_pengadaan(models.TransientModel):
    _name = 'logistik.edit.jenis.pengadaan'
    
    @api.model
    def default_get(self, fields):
        res = super(logistik_edit_jenis_pengadaan,self).default_get(fields)
        active_id = self._context.get('active_id', False)
        spm_line = self.env['logistik.spm.lines'].browse(active_id)
        if active_id:
            res['spm_line_id'] = active_id
            if not spm_line.product_id:
                res['category'] = 'noncode'
        return res
    
    spm_line_id = fields.Many2one('logistik.spm.lines', 'SPM Line')
    pengadaan = fields.Selection([('RD', 'Direksi'),('RP', 'Pabrik')], string='Ganti ke Jenis SP')
    reason = fields.Selection([('reason1','Barang tidak tersedia di wilayah kerja pengadaan lokal'),
                               ('reason2','Nilai barang melebihi batas maksimal pengadaan lokal'),
                               ('other','Lainnya')], 'Alasan')
    other_reason = fields.Text('Alasan Lain')
    category = fields.Selection([
        ('rab', 'RAB'),
        ('nonrab', 'Non RAB'),
        ('noncode', 'Tanpa Kode')
    ], string='Jenis SPM')
    
    
    @api.onchange('reason')
    def onchange_reason(self):
        if self.reason:
            if self.reason == 'reason1':
                self.other_reason = 'barang tidak tersedia di wilayah kerja pengadaan lokal.'
            if self.reason == 'reason2':
                self.other_reason = 'nilai barang melebihi batas maksimal pengadaan lokal.'
            if self.reason == 'other':
                self.other_reason = ''
                
    @api.multi
    def do_change_jenis_pengadaan(self):
        for this in self:
            this.spm_line_id.category = this.category
            this.spm_line_id.pengadaan = this.pengadaan
            
            if this.pengadaan=='RP':
                this.spm_line_id.action_approve()
            else:
                this.spm_line_id.action_validate()
                this.spm_line_id.btn_test='draft'
            this.spm_line_id.send_notification_edit_pengadaan(this.other_reason)
                
#             for line in this.pengajuan_spm_id.line_ids:
#                 if line.state in ('draftsp','sp','receive','done'):
#                     raise UserError('Jenis SP tidak dapat diubah karena barang sudah dalam proses SP Lokal')
            
        
#     @api.multi
#     def do_change_jenis_pengadaan(self):
#         for this in self:
#             this.pengajuan_spm_id.pengadaan = this.pengadaan
#             for line in this.pengajuan_spm_id.line_ids:
#                 line.pengadaan = this.pengadaan
#                 line.action_validate()
#             # followers                
#             follower_id = False
#             for follower in this.pengajuan_spm_id.message_follower_ids:
#                 if follower.partner_id.id == this.pengajuan_spm_id.user_id.partner_id.id:
#                     follower_id = follower.id
#                     break
#             followers = [(1, follower_id, {'subtype_ids': [(4, self.env.ref('ka_logistik_spm.mt_pengajuan_spm_edit_pengadaan').id)]})]
#             this.pengajuan_spm_id.write({'message_follower_ids': followers})
#             # get detail products
#             products = ''
#             for line in this.pengajuan_spm_id.line_ids:
#                 products += '- ' + line.product_id.display_name + ' (Jumlah : ' + str(line.kuantum_spm) + ' ' + line.unit_id.name + ')<br/>'
#             # send message
#             partner_ids = [this.pengajuan_spm_id.user_id.partner_id.id]
#             email = self.env.ref('ka_logistik_spm.template_notif_edit_jenis_spm')
#             base_template = email.body_html
#             content = '''%s'''%(email.body_html)
#             body_message = content%(products, this.other_reason)
#             email.write({'body_html': body_message})
#             post_vars = {'message_type': 'notification',
#                          'subtype_id': self.env.ref('ka_logistik_spm.mt_pengajuan_spm_edit_pengadaan').id,
#                          'needaction_partner_ids': partner_ids}
#             this.pengajuan_spm_id.message_post_with_template(email.id, **post_vars)
#             email.write({'body_html': base_template})
            
                