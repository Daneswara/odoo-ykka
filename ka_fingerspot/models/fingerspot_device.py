from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
import requests
import ast
from datetime import datetime, timedelta

class FingerspotDevice(models.Model):
	_name = 'ka_fingerspot.device'

	name = fields.Char(string="Nama", required=True)
	serial_number = fields.Char(string="Serial Number", size=32, required=True)
	server_id = fields.Many2one('ka_fingerspot.server', string="Server")
	last_get = fields.Datetime(string="Tanggal")
	new_presensi = fields.Integer(string="Terbaru", readonly=True)
	all_presensi = fields.Integer(string="Seluruhnya", readonly=True)
	users_registered = fields.Integer(string="Jumlah user terdaftar", readonly=True)
	faces_registered = fields.Integer(string="Jumlah Scan terdaftar", readonly=True)
	company_id = fields.Many2one('res.company', string="Unit/PG", default=lambda self:self.env.user.company_id)

	def get_serial_number(self):
		param = {
			'sn': self.serial_number
		}
		return param

	def _get_utc_timezone(self, asia_datetime):
		return asia_datetime - timedelta(hours=7)

	@api.model
	def set_log_message(self,command,log,state):
		vals = {
			'command': command,
			'log_message': log,
			'device_id': self.id,
			'state': state
		}
		self.env['ka_fingerspot.action.log'].create(vals)
		# return super(FingerspotDevice,self).create(vals)

	def action_get_info(self):
		try:
			url = 'http://'+self.server_id.ip_address+':'+str(self.server_id.port)+'/dev/info'
			r = requests.post(url, params=self.get_serial_number(), timeout=self.server_id.timeout)
			self.set_log_message('Get Info', 'Success', 'success')
			items = r.json()['DEVINFO'].items()
			for key, value in items:
				if key == 'Jam':
					asia_datetime = datetime.strptime(value, '%d/%m/%Y %H:%M:%S')
					self.last_get = self._get_utc_timezone(asia_datetime)
				if key == 'New Presensi':
					self.new_presensi = value
				if key == 'All Presensi':
					self.all_presensi = value
				if key == 'User':
					self.users_registered = value
				if key == 'Face':
					self.faces_registered = value
				# print key, value
			return True
		except requests.exceptions.RequestException as e:
			self.set_log_message('Get Info', e, 'error')
			return False

	def action_get_user(self):
		return

	def action_set_user(self):
		user = self.env['ka_fingerspot.user'].search([])
		for user_id in user:
			print user_id.name

	@api.one
	def action_get_user_all(self):
		try:
			lines = []
			url = 'http://'+self.server_id.ip_address+':'+str(self.server_id.port)+'/user/all'
			r = requests.post(url, params=self.get_serial_number(), timeout=self.server_id.timeout)
			self.set_log_message('Get All User', 'Success', 'success')
			for data in r.json()['Data']:
				if not self.env['ka_fingerspot.user'].search([('pin', '=', data['PIN'])]):
					for i in data['Template']:
						vals_lines = {
							'index': i['idx'],
							'alg_version': i['alg_ver'],
							'template': i['template']
						}
						lines.append((0,0,vals_lines))
					vals = {
						'pin': data['PIN'],
						'name': data['Name'],
						'password': data['Password'],
						'rfid': data['RFID'],
						'privilege': data['Privilege'],
						'template_lines': lines
						}
					self.env['ka_fingerspot.user'].create(vals)	
					# return {
						# 'name': 'All User',
						# 'view_type': 'form',
						# 'view_mode': 'tree',
						# 'res_model': 'ka_fingerspot.user',
						# 'type': 'ir.actions.act_window',
						# 'target': 'current',
					# }
		except requests.exceptions.RequestException as e:
			self.set_log_message('Get All User', e, 'error')

	def action_get_scan_new(self):
		if self.action_get_info():
			if self.new_presensi > 0:
				try:
					url = 'http://'+self.server_id.ip_address+':'+str(self.server_id.port)+'/scanlog/new'
					r = requests.post(url, params=self.get_serial_number(), timeout=self.server_id.timeout)
					self.set_log_message('Get New Log', 'Success', 'success')				
					for data in r.json()['Data']:
						user = self.env['ka_fingerspot.user'].search([('pin', '=', data['PIN'])]).id
						scan_date_obj = datetime.strptime(data['ScanDate'], DATETIME_FORMAT)
						vals = {
							'device_id': self.id,
							'serial_number': data['SN'],
							'scan_date': self._get_utc_timezone(scan_date_obj),
							'pin': data['PIN'],
							'verify_mode': data['VerifyMode'],
							'io_mode': data['IOMode'],
							'work_code': data['WorkCode'],
							'user_pin_id': user
						}
						self.env['ka_fingerspot.scanlog'].create(vals)
				except requests.exceptions.RequestException as e:
					self.set_log_message('Get New Scan', e, 'error')

	def action_get_scan_all(self):
		try:
			url = 'http://'+self.server_id.ip_address+':'+str(self.server_id.port)+'/scanlog/all'
			r = requests.post(url, params=self.get_serial_number(), timeout=self.server_id.timeout)
			self.set_log_message('Get All Scan', 'Success', 'success')
			for data in r.json()['Data']:
				user = self.env['ka_fingerspot.user'].search([('pin', '=', data['PIN'])]).id
				scan_date_obj = datetime.strptime(data['ScanDate'], DATETIME_FORMAT)
				vals = {
					'device_id': self.id,
					'serial_number': data['SN'],
					'scan_date': self._get_utc_timezone(scan_date_obj),
					'pin': data['PIN'],
					'verify_mode': data['VerifyMode'],
					'io_mode': data['IOMode'],
					'work_code': data['WorkCode'],
					'user_pin_id': user
				}
				self.env['ka_fingerspot.scanlog'].create(vals)
			
			return {
				'name': 'All Scan',
				'view_type': 'form',
				'view_mode': 'tree',
				'res_model': 'ka_fingerspot.scanlog',
				'type': 'ir.actions.act_window',
				'target': 'current',
			}
		except requests.exceptions.RequestException as e:
			self.set_log_message('Get All Scan', e, 'error')
