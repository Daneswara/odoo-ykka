from odoo import api, fields, models, _

class StockMove(models.Model):
    _inherit = "stock.move"
    
    spm_line_id = fields.Many2one('logistik.spm.lines', 'Sumber SPM', compute='_get_spm_line_id')
    spm_stasiun_id = fields.Many2one('account.analytic.stasiun', 'Stasiun Pemesan', compute='_get_spm_line_id')
    spm_user_id = fields.Many2one('res.users', 'Diminta Oleh', compute='_get_spm_line_id')
        
    
    @api.multi
    @api.depends('purchase_line_id')
    def _get_spm_line_id(self):
        for this in self:
            res = False
            backorder_location_usage = False
            purchase_line_id = False
            for move_orig in this.move_orig_ids:
                backorder_location_usage = move_orig.location_id.usage
                purchase_line_id = move_orig.purchase_line_id
                break
            admin_uid = self.env.ref('base.user_root').id
            if this.purchase_line_id:
                res = this.purchase_line_id.sudo(admin_uid).spm_line_id
            elif purchase_line_id and backorder_location_usage == 'supplier':
                res = purchase_line_id.sudo(admin_uid).spm_line_id
            if res:
                this.spm_line_id = res.id
                this.spm_stasiun_id = res.stasiun_id.id
                this.spm_user_id = res.pengajuan_id.user_id.id
            
    @api.multi
    def action_done(self):   
        super(StockMove, self).action_done()
        for this in self:
            #update SPM state when good is received
            if this.purchase_line_id and this.spm_line_id and this.location_id.usage=='supplier':
                this.spm_line_id.action_receive()

            #update SPM state when good release from QC
            backorder_location_usage = False
            purchase_line_id = False
            for move_orig in this.move_orig_ids:
                backorder_location_usage = move_orig.location_id.usage
                purchase_line_id = move_orig.purchase_line_id
                break
            if purchase_line_id and backorder_location_usage == 'supplier':
                purchase_line_id.spm_line_id.action_done()
