from odoo import models, fields, api

class Intesifikasi(models.Model):
	_name = 'ka_plantation.intensifikasi'
	_description = 'Intesifikasi Tanaman'
	_order = 'code'

	code = fields.Char(string="Kode", size=2, required=True)
	name = fields.Char(string="Nama", size=10, required=True)
	description = fields.Char(string="Keterangan", size=32)
	type = fields.Selection([('ts', 'TS'), ('tr', 'TR')], string='Jenis TS/TR')
	cost_template_ids = fields.One2many('ka_plantation.intensifikasi.cost.template', 'intensifikasi_id', string='Detail Biaya TS')


	_sql_constraints = [
		('ka_plantation_intesifikasi_code_unique', 'UNIQUE(code)', 'Kode sudah ada, silahkan masukkan kode lain!')
	]

	# # @override
	# @api.multi
	# def name_get(self):
		# res = []
		# for s in self:
			# code = s.code or ''
			# name = s.name or ''
			# res.append((s.id, code + ' - ' + name))

		# return res

	# # @override
	# @api.model
	# def name_search(self, name='', args=None, operator='ilike', limit=80):
		# if not args:
			# args = []

		# if name:
			# record = self.search([('code', operator, name)] + args, limit=limit)
			# if not record:
				# record = self.search([('name', operator, name)] + args, limit=limit)
		# else:
			# record = self.search(args, limit=limit)

		# return record.name_get()
		
class IntesifikasiCostTemplate(models.Model):
	_name = 'ka_plantation.intensifikasi.cost.template'
	_description = 'Template Biaya Pengadaan TS'
	
	name = fields.Char(string='Nama Biaya', size=32, required=True)
	account_code = fields.Char(string='Kode Perkiraan', size=8, company_dependent=True, required=False)
	product_id = fields.Many2one('product.product',string="Product")
	uom_id = fields.Many2one(string='Satuan Gudang', related='product_id.uom_id', readonly=True)
	intensifikasi_id = fields.Many2one('ka_plantation.intensifikasi', string='Intesifikasi', required=True, ondelete='cascade')
	is_ta = fields.Boolean('Biaya TA')
	
	