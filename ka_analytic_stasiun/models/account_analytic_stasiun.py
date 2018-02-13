from odoo import models, fields, api, SUPERUSER_ID

class account_analytic_stasiun(models.Model):
	_name = "account.analytic.stasiun"
	_description = "Master analisis Stasiun"
	_table = "account_analytic_stasiun"
	_inherits = {'account.analytic.account': 'account_analytic_id'}
		
	@api.multi
	def _get_full_name(self):
		for elmt in self:
			elmt.complete_name = self._get_one_full_name(elmt)

	def _get_one_full_name(self, elmt, level=6):
		if level<=0:
			return '...'
		if elmt.parent_id:
			parent_path = self._get_one_full_name(elmt.parent_id, level-1) + " / "
		else:
			parent_path = ''
		return parent_path + elmt.name
	
	complete_name = fields.Char(compute='_get_full_name', string='Full Name')
	department_id = fields.Many2one('hr.department', string='Bagian/Seksi')
	account_analytic_id = fields.Many2one('account.analytic.account', string='Account Analytic', required=True, ondelete='cascade')
	child_ids = fields.One2many('account.analytic.stasiun','parent_id',string="Children")
	parent_id = fields.Many2one('account.analytic.stasiun',string='Parent',domain=[('analytic_type', '=', 'view')])

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

	@api.one
	def _stasiun_default_get(self):
		user = self.env['res.users'].browse(SUPERUSER_ID)
		stasiun = []
		self.error_untuk_direvisi
		if user.stasiun_ids:
			stasiun = user.stasiun_ids.id
		return stasiun
	
	# override
	@api.multi
	def unlink(self):
		aa_ids = []
		for s in self:
			aa_ids.append(s.account_analytic_id.id)
		super(account_analytic_stasiun, self).unlink()
		return self.env['account.analytic.account'].search([('id' , 'in', aa_ids)]).unlink()
	
	# override
	@api.model
	def create(self, vals):
		vals['is_stasiun'] = True
		ret = super(account_analytic_stasiun, self).create(vals)
		if ret:
			ret.account_analytic_id.stasiun_id = ret.id
		return ret
		