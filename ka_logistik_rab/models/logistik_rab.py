from odoo import models, fields, api, exceptions
from datetime import date

class logistik_rab(models.Model):
	_name = 'logistik.rab'
	_description = "RAB"
	_rec_name="account_id"
		
	tahun = fields.Many2one('ka.account.fiscalyear', string='Tahun Anggaran', required=True)
	# stasiun_id = fields.Many2one('account.analytic.stasiun', string='Stasiun', domain="[('type', '=', 'normal'), ('company_id', '=', company_id)]", required=True)
	stasiun_id = fields.Many2one('account.analytic.stasiun', string='Stasiun', required=True)
	account_id = fields.Many2one('account.account', string='No. Perkiraan', required=True)
	total_rab = fields.Float(compute='_compute_anggaran', string='Total RAB', digits=(16, 2), store=True)
	line_ids = fields.One2many('logistik.rab.lines', 'rab_id', 'Detail Barang')
	company_id = fields.Many2one('res.company', 'Unit/PG', required=True, default=lambda self: self.env['res.company']._company_default_get('logistik.rab'))
	user_id = fields.Many2one('res.users', string='Di Entry Oleh', default=lambda self: self._uid)
	department_id = fields.Many2one(string='Bagian', related='stasiun_id.department_id', store=True)
		
	_sql_constraints = [('perk_unique', 'unique(account_id, company_id)', 'Nomer Perkiraan tidak boleh dobel!'),]

	@api.depends('line_ids.kuantum', 'line_ids.harga')
	def _compute_anggaran(self):
		for s in self:
			total = 0
			for line in s.line_ids:
				total += line.kuantum * line.harga
			s.total_rab = total

	@api.onchange('account_id')
	def onchange_account_id(self):
		if not self.account_id or not self.account_id.code:
			return
		
		perk = self.account_id.code[:6]
		perk = perk[:1]+'0'+perk[2:]
		id = self.env['account.analytic.stasiun'].search([('code', '=', perk)])
		if id:
			self.stasiun_id = id[0]
		else:
			raise exceptions.Warning('Stasiun untuk Nomor Perkiraan Tersebut belum Terdaftar')

	@api.multi
	def get_rab_available(self, params):
		res = []
		if params['account_id'] and params['prod_id'] and params['tahun']:
			self._cr.execute('SELECT r.id from logistik_rab r '\
				'INNER JOIN logistik_rab_lines l ON (l.rab_id = r.id AND '\
				'r.account_id = %s AND l.product_id = %s '\
				'AND r.tahun = %s)' % ( "'"+str(params['account_id'])+"'",  params['prod_id'],  params['tahun']))
			res =  self._cr.fetchone()
		return res and res[0] or False

	@api.model
	def create(self, vals):
		if self._check_value(vals):
			return super(logistik_rab, self).create(vals)

	@api.multi
	def write(self, vals):
		if self._check_value(vals):
			return super(logistik_rab, self).write(vals)

	def _check_value(self, value):
		if not value.has_key('line_ids') or not value['line_ids']:
			raise exceptions.Warning('Item barang harus diisi!')
			return False

		for line in value['line_ids']:
			if not line[2]:
				continue
			if line[2].has_key('kuantum') and int(line[2]['kuantum']) <= 0:
				raise exceptions.Warning('Kuantum barang harus diisi!')
				return False
			if line[2].has_key('harga') and int(line[2]['harga']) <= 0:
				raise exceptions.Warning('Harga barang harus diisi!')
				return False

		return True