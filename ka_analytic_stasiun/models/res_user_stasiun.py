from odoo import models, fields, api

class res_user_stasiun(models.Model):
	_inherit = 'res.users'

	stasiun_ids = fields.Many2many('account.analytic.stasiun', 'rel_user_stasiun', 'user_id', 'stasiun_id', string='Stasiun/Divisi')