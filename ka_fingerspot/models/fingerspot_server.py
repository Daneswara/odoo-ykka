from odoo import models, fields, api

class FingerspotServer(models.Model):
	_name = 'ka_fingerspot.server'

	name = fields.Char(string="Nama", required=True)
	company_id = fields.Many2one('res.company', string="Unit/PG", default=lambda self:self.env.user.company_id)
	ip_address = fields.Char(string="Ip Address", required=True)
	port = fields.Integer(string="Port", required=True)
	timeout = fields.Integer(string="Time Out", required=True, default=120)
	fingerspot_device = fields.One2many('ka_fingerspot.device','server_id', string="Device")