from odoo import models, fields, api

class MTT(models.Model):
	_name = 'ka_plantation.mtt'
	_order = 'name desc'

	name = fields.Char(string="M T T", size=9)
	session_id = fields.Many2one('ka_manufacture.session',string="Masa Giling",required=True)
	luas = fields.Float(string="Luas",compute="_compute_sum")
	taks_produksi = fields.Float(compute='_compute_sum', string="Taks. Produksi")
	count_register = fields.Integer(string="Jml. Register", compute="_compute_sum")
	register_ids = fields.One2many('ka_plantation.register', 'mtt_id', string="Register")
	state = fields.Selection([("draft", "Draft"),
                              ("open", "Open"),
                              ("close", "Close")],
                                string = "Status", default="draft")
	
	def open_register(self):
		company = self._get_user_companies()
		action = self.env.ref('ka_tanaman.action_register')
		result = action.read()[0]
		result['domain'] = [('mtt_id', '=', self.id), ('register_type', '!=', 'ts'), ('company_id', 'in', company)]
		result['context'] = {
			'default_mtt_id': self.id,
		}
		return result

	def open_register_ts(self):
		company = self._get_user_companies()
		action = self.env.ref('ka_tanaman.action_register_ts')
		result = action.read()[0]
		result['domain'] = [('mtt_id', '=', self.id), ('register_type', '=', 'ts'), ('company_id', 'in', company)]
		result['context'] = {
			'default_mtt_id': self.id,
			'default_register_type': 'ts',
		}
		return result
		
	def open_register_lines(self):
		company = self._get_user_companies()
		registers = [reg.id for reg in self.register_ids]
		action = self.env.ref('ka_tanaman.action_register_lines')
		result = action.read()[0]
		result['domain'] = [('register_id', 'in', registers), ('register_id.company_id', 'in', company)]
		return result

	def _get_user_companies(self):
		return [company.id for company in self.env.user.company_ids]
	
	@api.multi
	@api.depends('register_ids')
	def _compute_sum(self):
		company = self._get_user_companies()
		str_company = "("
		for c in company:
			str_company += str(c) + ","

		str_company = str_company[:-1]
		str_company += ")"
		check_context = self.env.context.get('default_register_type')
		for s in self:
			sql = ''
			if check_context == 'ts':
				sql = """SELECT 
						sum(r.luas), 
						sum(r.taks_produksi), 
						count(r.id)
					FROM 
						ka_plantation_register r
					WHERE 
						r.mtt_id=%s AND r.register_type='%s' AND r.company_id IN %s
					LIMIT 1;""" %(str(s.id), 'ts', str_company)
			else:
				sql = """SELECT 
							sum(r.luas), 
							sum(r.taks_produksi), 
							count(r.id)
					FROM 
						ka_plantation_register r
					WHERE 
						r.mtt_id=%s AND r.register_type!='%s' AND r.company_id IN %s
					LIMIT 1;""" %(str(s.id), 'ts', str_company)

			s._cr.execute(sql)
			cek = s._cr.fetchall()
			for luas, taks, countid in cek:
				s.luas = luas
				s.taks_produksi = taks
				s.count_register = int(countid)
				break
				
	@api.one
	def action_open(self):
		self.state = 'open'

	@api.one
	def action_close(self):
		self.state = 'close'

	@api.one
	def action_set_draft(self):
		self.state = 'draft'