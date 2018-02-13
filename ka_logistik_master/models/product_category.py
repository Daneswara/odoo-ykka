from odoo import models, fields, api

class product_category(models.Model):
	_inherit = 'product.category'
	_order = 'code'

	#Disable Translation
	name = fields.Char('Name', index=True, required=True, translate=False)
	
	code = fields.Char(string='Kode', size=16, required=True)
	specification = fields.Text(string='Spesifikasi')
	
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
		
		
class ProductUoMCategory(models.Model):
	_inherit = 'product.uom.categ'

	name = fields.Char('Name', required=True, translate=False)


#Disable Translation
class ProductUoM(models.Model):
	_inherit = 'product.uom'

	name = fields.Char('Unit of Measure', required=True, translate=False)