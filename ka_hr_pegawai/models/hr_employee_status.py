# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api

class KaHrEmployeeStatus(models.Model):
    """Master data of employee status (staf, pelaksana)

    _name = 'hr.employee.status'
    """

    _name = 'hr.employee.status'

    code = fields.Char(string="Kode", size=6, required=True)
    name = fields.Char(string="Nama Status", size=64, required=True)
    parent_id = fields.Many2one('hr.employee.status', string="Parent")
    child_ids = fields.One2many('hr.employee.status', 'parent_id', string="Childs")
    employee_ids = fields.One2many('hr.employee', 'status_id', string="Karyawan")

    _sql_constraints = [
        ('hr_employee_status_unique', 'UNIQUE(code)', "Kode sudah digunakan. Silakan gunakan kode lain.")
    ]

    @api.multi
    def name_get(self):
        """Get representative name for this model.
        Override from method `name_get()`.

        Decorators:
            api.multi
        """
        res = []
        for status in self:
            code = status.code or ''
            name = status.name or ''
            res.append((status.id, '{0} - {1}'.format(code, name)))

        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=80):
        """To searching this model by representative name in method `name_get()`.
        Override from method `name_search()`.

        Decorators:
            api.model

        Keyword Arguments:
            name {String} -- Query string to search (default: {''})
            args {List} -- Added args for search query (default: {None})
            operator {String} -- Operator condition for search query (default: {'ilike'})
            limit {Int} -- Limit data search query (default: {80})
        """
        if not args:
            args = []

        if name:
            record = self.search(['|', ('name', operator, name), ('code', operator, name)] + args, limit=limit)
        else:
            record = self.search(args, limit=limit)

        return record.name_get()
