from datetime import datetime
from odoo import models, fields, api

class ka_account_fiscalyear(models.Model):
    _name = 'ka.account.fiscalyear'
    _description = 'Fiscal Year'

    code = fields.Char(string='Code', size=6, required=True)
    # name = fields.Char(string='Fiscal Year', required=True)
    name = fields.Selection([
        (str(num), str(num)) for num in range((datetime.now().year)+5, (datetime.now().year)-10, -1)
    ], string='Fiscal Year', required=True)

    # @override
    @api.multi
    def name_get(self):
        res = []
        for s in self:
            code = s.code or ''
            name = s.name or ''
            res.append((s.id, code + ' - ' + name))

        return res

    # @override
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=80):
        if not args:
            args = []

        if name:
            record = self.search([('code', operator, name)] + args, limit=limit)
            if not record:
                record = self.search([('name', operator, name)] + args, limit=limit)
        else:
            record = self.search(args, limit=limit)

        return record.name_get()