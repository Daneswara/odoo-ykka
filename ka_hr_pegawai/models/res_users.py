# ----------------------------------------------------------
# Data departemen yg dimiliki oleh user
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields

class res_users(models.Model):
	_inherit = 'res.users'
	
	department_ids = fields.Many2many('hr.department', 'rel_user_department', 'user_id', 'department_id', string='Departemen/Divisi')