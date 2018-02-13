from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from datetime import datetime, timedelta

class FingerspotScanlog(models.Model):
	_name = 'ka_fingerspot.scanlog'

	device_id = fields.Many2one('ka_fingerspot.device', string="Device")
	serial_number = fields.Char(string="Serial Number", size=32)
	scan_date = fields.Datetime(string="Tanggal Scan")
	date_scan_date = fields.Date(compute='_compute_scan_date', store=True) # helper agar bisa mengambil berdasarkan date
	pin = fields.Char(string="No. Pin", size=16)
	verify_mode = fields.Integer(string="Mode Verifikasi")
	io_mode = fields.Integer(string="Mode Input dan Output")
	work_code = fields.Integer(string="Kode Kerja")
	user_pin_id = fields.Many2one('ka_fingerspot.user', string="User")
	company_id = fields.Many2one(string="Unit/PG", related='device_id.company_id', readonly=True, store=True)

	def _get_asia_timezone(self, utc_datetime):
		return utc_datetime + timedelta(hours=7)

	@api.depends('scan_date')
	def _compute_scan_date(self):
		for s in self:
			scan_date_obj = datetime.strptime(s.scan_date, DATETIME_FORMAT)
			s.date_scan_date = s._get_asia_timezone(scan_date_obj).date()

	# @override
	@api.multi
	def name_get(self):
		res = []
		for s in self:
			device = s.device_id.name or ''
			name = s.pin or ''
			res.append((s.id, device + ' - ' + name))
		return res

	# @override
	@api.model
	def name_search(self, name='', args=None, operator='ilike', limit=80):
		if not args:
			args = []

		if name:
			record = self.search([('name', operator, name)] + args, limit=limit)
		else:
			record = self.search(args, limit=limit)

		return record.name_get()