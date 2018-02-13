import json
from odoo import models, api

class res_users(models.Model):
	_inherit = 'res.users'

	@api.model
	@api.multi
	def get_current_user(self):
		user = self.browse(self._uid)
		data = {'id': user.id, 'company_id': user.company_id.id}
		return json.dumps(data, ensure_ascii=False)
