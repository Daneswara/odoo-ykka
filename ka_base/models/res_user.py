from odoo import models, fields, api

class res_user_stasiun(models.Model):
    _inherit = 'res.users'
    
    ################## FROM BASE MODULE ################
    def _default_groups(self):
        default_user = self.env.ref('base.default_user', raise_if_not_found=False)
        return (default_user or self.env['res.users']).sudo().groups_id
    
    groups_id = fields.Many2many('res.groups', 'res_groups_users_rel', 'uid', 'gid', string='Groups', default=_default_groups)
    ####################################################

    @api.model
    def operating_unit_default_get(self, uid2):
        if not uid2:
            uid2 = self._uid
        user = self.env['res.users'].browse(uid2)
        return user.default_operating_unit_id
    
    @api.one
    @api.depends('company_id')
    def _set_operating_unit(self):
        self.default_operating_unit_id = self.company_id.partner_id.id


    @api.one
    @api.depends('company_ids')
    def _set_operating_units(self):
        ou_ids = [c.partner_id.id for c in self.company_ids]
        self.operating_unit_ids = ou_ids
        
        
    default_operating_unit_id = fields.Many2one('res.partner', 'Default Unit/PG', compute='_set_operating_unit', store=True)	
    operating_unit_ids = fields.Many2many('res.partner', string="Unit/PG", compute='_set_operating_units', store=True)
    