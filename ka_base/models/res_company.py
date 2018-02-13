from openerp.osv import expression
from odoo import api, fields, models, SUPERUSER_ID

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    intercompany_user_id = fields.Many2one("res.users", string="User R/K", default=SUPERUSER_ID, help="User yang akan melakukan R/K secara otomatis")
    internal_user_id = fields.Many2one("res.users", string="Internal User", default=SUPERUSER_ID, help="Internal user for this company")
    code = fields.Char("Code", size=1)
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        companies = self.search(domain + args, limit=limit)
        return companies.name_get()

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for company in self:
            name = company.name
            if company.code:
                name = company.code + ' ' + company.name
            result.append((company.id, name))
        return result

    def get_internal_user(self):
        return self.internal_user_id.id
   
